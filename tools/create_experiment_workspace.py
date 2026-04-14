from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sim.task_spec import load_task_spec


EXPERIMENTS_ROOT = REPO_ROOT / "experiments"
BASE_WORKSPACE_ROOT = EXPERIMENTS_ROOT / "base_workspace"
COMMON_ROOT = EXPERIMENTS_ROOT / "common"
TASKS_ROOT = EXPERIMENTS_ROOT / "tasks"
DEFAULT_LOCAL_PATHS = ["agent_tests"]
DEFAULT_PUBLIC_TASK_CONTRACT_MODE = "prose_only"
PUBLIC_TASK_CONTRACT_MODES = {"prose_only", "json"}
SELF_VERIFICATION_LOCAL_PATHS = ("agent_tests",)
SELF_VERIFICATION_VISIBLE_PATHS = (
    Path("agent_tests"),
    Path("bench_public"),
    Path("tools/run_build.py"),
    Path("tools/run_self_tests.py"),
)


def _git_init(target: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=target, check=True)
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "Initialize experiment workspace"], cwd=target, check=True)


def _available_task_ids() -> list[str]:
    if not TASKS_ROOT.exists():
        return []
    return sorted(child.name for child in TASKS_ROOT.iterdir() if child.is_dir())


def _load_task(task_id: str) -> tuple[Path, dict[str, object]]:
    task_root = TASKS_ROOT / task_id
    if not task_root.exists():
        available = _available_task_ids()
        if available:
            available_text = ", ".join(available)
            raise SystemExit(f"unknown task_id: {task_id}\navailable task ids: {available_text}")
        raise SystemExit(f"unknown task_id: {task_id}")

    manifest_path = task_root / "task.json"
    if not manifest_path.exists():
        raise SystemExit(f"missing task manifest: {manifest_path}")

    return task_root, json.loads(manifest_path.read_text(encoding="utf-8"))


def _copy_tree(source: Path, target: Path) -> None:
    shutil.copytree(source, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def _resolve_public_task_contract_mode(
    manifest: dict[str, object],
    public_task_contract_mode: str,
) -> str:
    if public_task_contract_mode:
        mode = public_task_contract_mode
    else:
        raw_config = manifest.get("public_task_contract", DEFAULT_PUBLIC_TASK_CONTRACT_MODE)
        if isinstance(raw_config, dict):
            mode = str(raw_config.get("mode", DEFAULT_PUBLIC_TASK_CONTRACT_MODE))
        else:
            mode = str(raw_config)
    mode = mode.strip() or DEFAULT_PUBLIC_TASK_CONTRACT_MODE
    if mode not in PUBLIC_TASK_CONTRACT_MODES:
        available = ", ".join(sorted(PUBLIC_TASK_CONTRACT_MODES))
        raise SystemExit(
            f"unsupported public task contract mode: {mode}. available modes: {available}"
        )
    return mode


def _write_docs(
    target: Path,
    task_root: Path,
    manifest: dict[str, object],
    public_task_contract_mode: str,
) -> None:
    docs_dir = target / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(COMMON_ROOT / "agent_workflow.md", docs_dir / "00_common_instructions.md")

    task_spec_path = str(manifest.get("task_spec_path", "")).strip()
    task_spec = load_task_spec(REPO_ROOT / task_spec_path) if task_spec_path else None

    task_doc_path = task_root / "task.md"
    if task_doc_path.exists():
        shutil.copy2(task_doc_path, docs_dir / "10_task.md")
    elif task_spec is not None:
        (docs_dir / "10_task.md").write_text(task_spec.render_agent_summary(), encoding="utf-8")
    else:
        raise SystemExit(f"task {manifest['task_id']} must provide task.md or task_spec_path")

    if task_spec is not None and public_task_contract_mode == "json":
        (docs_dir / "20_task_contract.json").write_text(
            json.dumps(task_spec.public_contract_payload(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _resolve_benchmark(manifest: dict[str, object], benchmark_mode: str) -> dict[str, object]:
    benchmark = dict(manifest.get("benchmark", {}))
    if benchmark_mode:
        benchmark["mode"] = benchmark_mode
    return benchmark


def _benchmark_mode(benchmark: dict[str, object]) -> str:
    return str(benchmark.get("mode", "realistic_self_verify")).strip() or "realistic_self_verify"


def _self_verification_enabled(benchmark: dict[str, object]) -> bool:
    return _benchmark_mode(benchmark) != "oneshot_blind"


def _is_under(path: str, roots: tuple[str, ...]) -> bool:
    return any(path == root or path.startswith(f"{root}/") for root in roots)


def _filter_local_paths(local_paths: list[str], benchmark: dict[str, object]) -> list[str]:
    if _self_verification_enabled(benchmark):
        return local_paths
    return [path for path in local_paths if not _is_under(path, SELF_VERIFICATION_LOCAL_PATHS)]


def _remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
        return
    path.unlink()


def _prune_visible_self_verification(target: Path, benchmark: dict[str, object]) -> None:
    if _self_verification_enabled(benchmark):
        return
    for relative in SELF_VERIFICATION_VISIBLE_PATHS:
        _remove_path(target / relative)


def _write_experiment_json(
    target: Path,
    manifest: dict[str, object],
    benchmark: dict[str, object],
    public_task_contract_mode: str,
) -> None:
    editable_paths = list(manifest["editable_paths"])
    sync_paths = list(manifest.get("sync_paths", editable_paths))
    local_paths = _filter_local_paths(list(manifest.get("local_paths", DEFAULT_LOCAL_PATHS)), benchmark)
    task_docs = [
        "START_HERE.md",
        "docs/00_common_instructions.md",
        "docs/10_task.md",
    ]
    if public_task_contract_mode == "json":
        task_docs.append("docs/20_task_contract.json")
    payload = {
        "task_id": manifest["task_id"],
        "task_name": manifest["task_name"],
        "task_version": manifest["task_version"],
        "editable_paths": editable_paths,
        "sync_paths": sync_paths,
        "local_paths": local_paths,
        "feedback": manifest.get("feedback", {}),
        "benchmark": benchmark,
        "public_task_contract": {"mode": public_task_contract_mode},
        "task_docs": task_docs,
    }
    (target / "experiment.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a fresh visible workspace for an experiment task.")
    parser.add_argument("task_id", help="Task identifier under experiments/tasks/.")
    parser.add_argument("target", type=Path, help="Destination path for the generated visible workspace.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace the destination if it already exists.",
    )
    parser.add_argument(
        "--skip-git-init",
        action="store_true",
        help="Copy files only and do not initialize a git repository in the destination.",
    )
    parser.add_argument(
        "--benchmark-mode",
        default="",
        help="Optional benchmark mode override for the generated visible workspace.",
    )
    parser.add_argument(
        "--public-task-contract",
        default="",
        help="Optional visible task-contract mode override: prose_only (default) or json.",
    )
    args = parser.parse_args()

    task_root, manifest = _load_task(args.task_id)
    target = args.target.resolve()
    if target.exists():
        if not args.force:
            raise SystemExit(f"{target} already exists; use --force to replace it")
        shutil.rmtree(target)

    benchmark = _resolve_benchmark(manifest, args.benchmark_mode)
    public_task_contract_mode = _resolve_public_task_contract_mode(manifest, args.public_task_contract)
    _copy_tree(BASE_WORKSPACE_ROOT, target)
    _copy_tree(task_root / "visible_files", target)
    _prune_visible_self_verification(target, benchmark)
    _write_docs(target, task_root, manifest, public_task_contract_mode)
    _write_experiment_json(target, manifest, benchmark, public_task_contract_mode)

    if not args.skip_git_init:
        _git_init(target)

    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
