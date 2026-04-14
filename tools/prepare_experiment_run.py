from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_ROOT = REPO_ROOT / "experiments" / "results"


def _safe_slug(value: str) -> str:
    allowed = []
    for char in value:
        if char.isalnum() or char in "._-":
            allowed.append(char)
        else:
            allowed.append("-")
    slug = "".join(allowed).strip(".-")
    return slug or "unspecified"


def _create_workspace(
    task_id: str,
    workspace: Path,
    force: bool,
    skip_git_init: bool,
    benchmark_mode: str,
    public_task_contract: str,
) -> None:
    command = [
        "python3",
        str(REPO_ROOT / "tools" / "create_experiment_workspace.py"),
        task_id,
        str(workspace),
    ]
    if force:
        command.append("--force")
    if skip_git_init:
        command.append("--skip-git-init")
    if benchmark_mode:
        command.extend(["--benchmark-mode", benchmark_mode])
    if public_task_contract:
        command.extend(["--public-task-contract", public_task_contract])
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "workspace creation failed"
        raise SystemExit(message)


def _snapshot_repo_files() -> list[Path]:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
        text=False,
    )
    raw_paths = completed.stdout.decode("utf-8").split("\0")
    return [Path(raw_path) for raw_path in raw_paths if raw_path]


def _create_hidden_harness_root(task_id: str, agent_name: str, timestamp: str, harness_root: Path | None) -> Path:
    if harness_root is not None:
        return harness_root.resolve()

    snapshot_root = Path("/tmp") / "embedded_eval_hidden_harness" / task_id / (
        f"{_safe_slug(agent_name)}_{timestamp}"
    )
    if snapshot_root.exists():
        shutil.rmtree(snapshot_root)
    snapshot_root.mkdir(parents=True, exist_ok=True)

    for relative_path in _snapshot_repo_files():
        source = REPO_ROOT / relative_path
        if not source.exists():
            continue
        target = snapshot_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return snapshot_root.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare a visible experiment workspace and emit the hidden evaluator environment for launching an agent."
    )
    parser.add_argument("task_id", help="Task identifier under experiments/tasks/.")
    parser.add_argument("workspace", type=Path, help="Target path for the generated visible workspace.")
    parser.add_argument("--agent-name", default="unspecified-agent")
    parser.add_argument("--run-label", default="")
    parser.add_argument(
        "--benchmark-mode",
        default="",
        help="Optional benchmark mode override written into the visible workspace.",
    )
    parser.add_argument(
        "--public-task-contract",
        default="",
        help="Optional visible task-contract mode override written into the visible workspace.",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-git-init", action="store_true")
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument(
        "--harness-root",
        type=Path,
        default=None,
        help="Optional existing hidden harness root. If omitted, a snapshot of the current repo state is created automatically.",
    )
    parser.add_argument(
        "--hidden-run-root",
        type=Path,
        default=None,
        help="Optional hidden run root. Defaults to a fresh directory under /tmp.",
    )
    parser.add_argument(
        "--shell-exports",
        action="store_true",
        help="Print shell export commands only, suitable for eval.",
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    _create_workspace(
        args.task_id,
        workspace,
        args.force,
        args.skip_git_init,
        args.benchmark_mode,
        args.public_task_contract,
    )

    launch_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    harness_root = _create_hidden_harness_root(args.task_id, args.agent_name, launch_timestamp, args.harness_root)
    hidden_run_root = args.hidden_run_root
    if hidden_run_root is None:
        hidden_run_root = Path("/tmp") / "embedded_eval_hidden_runs" / args.task_id / (
            f"{_safe_slug(args.agent_name)}_{launch_timestamp}"
        )
    hidden_run_root = hidden_run_root.resolve()
    hidden_run_root.mkdir(parents=True, exist_ok=True)

    results_root = args.results_root.resolve()
    results_root.mkdir(parents=True, exist_ok=True)

    env_map = {
        "EMBEDDED_EVAL_HARNESS_ROOT": str(harness_root),
        "EMBEDDED_EVAL_RUN_ROOT": str(hidden_run_root),
        "EMBEDDED_EVAL_RESULTS_ROOT": str(results_root),
        "EMBEDDED_EVAL_AGENT_NAME": args.agent_name,
    }
    if args.benchmark_mode:
        env_map["EMBEDDED_EVAL_BENCHMARK_MODE"] = args.benchmark_mode
    if args.run_label:
        env_map["EMBEDDED_EVAL_RUN_LABEL"] = args.run_label

    if args.shell_exports:
        for key, value in env_map.items():
            print(f"export {key}={shlex.quote(value)}")
        return 0

    print(f"Workspace: {workspace}")
    print(f"Task: {args.task_id}")
    print(f"Agent name: {args.agent_name}")
    if args.benchmark_mode:
        print(f"Benchmark mode: {args.benchmark_mode}")
    if args.public_task_contract:
        print(f"Public task contract: {args.public_task_contract}")
    if args.run_label:
        print(f"Run label: {args.run_label}")
    print(f"Hidden harness root: {harness_root}")
    print(f"Hidden run root: {hidden_run_root}")
    print("")
    print("Launch the agent with these environment variables:")
    for key, value in env_map.items():
        print(f"{key}={value}")
    print("")
    print("Next step:")
    print(f"  cd {workspace}")
    print("  <launch your agent here and tell it to follow START_HERE.md>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
