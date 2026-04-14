from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.feedback import normalize_feedback_config, project_feedback, render_feedback_markdown
from sim.task_spec import TaskSpec, load_task_spec


PASS = "PASS"
HOST_TEST_FAILED = "HOST_TEST_FAILED"
BUILD_FAILED = "BUILD_FAILED"
FLASH_IMAGE_FAILED = "FLASH_IMAGE_FAILED"
QEMU_SMOKE_FAILED = "QEMU_SMOKE_FAILED"
INTEGRATION_FAILED = "INTEGRATION_FAILED"
EDIT_SURFACE_VIOLATION = "EDIT_SURFACE_VIOLATION"

DEFAULT_TASK_SPEC = Path(__file__).resolve().parents[1] / "specs" / "tank_fill_drain.json"
FIRMWARE_SNAPSHOT_PATHS = [
    "CMakeLists.txt",
    "sdkconfig.defaults",
    "main",
    "components/controller",
    "components/protocol",
]
DEFAULT_DIFF_PATHS = [
    "main",
    "components/controller",
    "components/protocol",
]


@dataclass(frozen=True)
class Stage:
    name: str
    command: list[str]
    failure_status: str
    artifact_dir_name: str
    extra_env: dict[str, str]


def _read_tail(path: Path, line_count: int = 40) -> str:
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-line_count:])


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_problem_lines(text: str, tokens: tuple[str, ...], limit: int = 20) -> list[str]:
    matches = [line.strip() for line in text.splitlines() if any(token in line.lower() for token in tokens)]
    return matches[-limit:]


def _run_command(repo_root: Path, command: list[str], env: dict[str, str], artifact_dir: Path) -> dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = artifact_dir / "stdout.log"
    stderr_path = artifact_dir / "stderr.log"
    start = time.monotonic()
    with stdout_path.open("w", encoding="ascii") as stdout_handle, stderr_path.open("w", encoding="ascii") as stderr_handle:
        try:
            completed = subprocess.run(
                command,
                cwd=repo_root,
                env=env,
                stdout=stdout_handle,
                stderr=stderr_handle,
                text=True,
                check=False,
            )
            returncode = completed.returncode
        except FileNotFoundError as exc:
            stderr_handle.write(f"{exc}\n")
            returncode = 127

    duration_s = round(time.monotonic() - start, 3)
    stdout_text = _read_text(stdout_path)
    stderr_text = _read_text(stderr_path)
    stdout_tail = _read_tail(stdout_path)
    stderr_tail = _read_tail(stderr_path)
    error_lines = _extract_problem_lines(
        "\n".join([stdout_text, stderr_text]),
        tokens=("error", "failed", "timeout", "exception", "traceback"),
    )
    warning_lines = _extract_problem_lines("\n".join([stdout_text, stderr_text]), tokens=("warning",))

    return {
        "returncode": returncode,
        "success": returncode == 0,
        "duration_s": duration_s,
        "stdout_path": stdout_path,
        "stderr_path": stderr_path,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "errors": error_lines,
        "warnings": warning_lines,
    }


def _is_git_repo(repo_root: Path) -> bool:
    completed = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0 and completed.stdout.strip() == "true"


def _changed_paths(repo_root: Path) -> list[str]:
    if not _is_git_repo(repo_root):
        return []
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    paths: list[str] = []
    for line in completed.stdout.splitlines():
        if line:
            paths.append(line[3:])
    return paths


def _validate_edit_surface(repo_root: Path, allowed_paths: list[str]) -> tuple[bool, list[str]]:
    if not allowed_paths:
        return True, []

    violations = []
    for path in _changed_paths(repo_root):
        if path.startswith("artifacts/"):
            continue
        if any(path == allowed or path.startswith(f"{allowed}/") for allowed in allowed_paths):
            continue
        violations.append(path)
    return len(violations) == 0, violations


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _copy_snapshot_entry(repo_root: Path, relative_path: str, target_root: Path) -> None:
    source = repo_root / relative_path
    target = target_root / relative_path
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _capture_firmware_snapshot(repo_root: Path, run_dir: Path) -> None:
    snapshot_root = run_dir / "firmware"
    snapshot_root.mkdir(parents=True, exist_ok=True)
    for relative_path in FIRMWARE_SNAPSHOT_PATHS:
        _copy_snapshot_entry(repo_root, relative_path, snapshot_root)


def _git_text(repo_root: Path, args: list[str]) -> str:
    if not _is_git_repo(repo_root):
        return ""
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip()


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_agent_response_proxy(repo_root: Path, run_dir: Path, allowed_paths: list[str]) -> None:
    diff_paths = allowed_paths or DEFAULT_DIFF_PATHS
    if not _is_git_repo(repo_root):
        _write_text(run_dir / "agent_response.txt", "Git diff is unavailable in this harness snapshot.\n")
        return
    completed = subprocess.run(
        ["git", "diff", "--", *diff_paths],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    diff_text = completed.stdout.strip()
    if not diff_text:
        diff_text = "No git diff is available for the selected paths.\n"
    _write_text(run_dir / "agent_response.txt", diff_text if diff_text.endswith("\n") else diff_text + "\n")


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_history(run_parent: Path, current_run_dir: Path) -> list[dict[str, Any]]:
    if not run_parent.exists():
        return []

    entries: list[dict[str, Any]] = []
    for child in sorted(run_parent.iterdir()):
        if not child.is_dir() or child == current_run_dir:
            continue
        feedback_path = child / "feedback.json"
        if not feedback_path.exists():
            continue
        payload = _load_json_if_exists(feedback_path)
        summary = payload.get("summary", {})
        entries.append(
            {
                "trial_id": child.name,
                "status": summary.get("status"),
                "task_solved": summary.get("task_solved", False),
                "failure_category": summary.get("failure_category"),
            }
        )
    return entries[-10:]


def _scenario_dirs(integration_dir: Path) -> list[Path]:
    if not integration_dir.exists():
        return []
    return sorted(child for child in integration_dir.iterdir() if child.is_dir())


def _pick_preferred_scenario_dir(run_dir: Path) -> Path | None:
    integration_dir = run_dir / "integration"
    for scenario_dir in _scenario_dirs(integration_dir):
        summary = _load_json_if_exists(scenario_dir / "summary.json")
        if summary and not summary.get("passed", False):
            return scenario_dir
    scenario_dirs = _scenario_dirs(integration_dir)
    if scenario_dirs:
        return scenario_dirs[0]
    smoke_dir = run_dir / "qemu_smoke"
    if smoke_dir.exists():
        return smoke_dir
    return None


def _collect_uart_excerpt(run_dir: Path, repo_root: Path) -> dict[str, Any]:
    scenario_dir = _pick_preferred_scenario_dir(run_dir)
    if scenario_dir is None:
        return {}
    transcript_path = scenario_dir / "transcript.log"
    return {
        "path": _display_path(transcript_path, repo_root),
        "excerpt": _read_tail(transcript_path, line_count=25),
    }


def _collect_trace_excerpt(run_dir: Path, repo_root: Path) -> dict[str, Any]:
    scenario_dir = _pick_preferred_scenario_dir(run_dir)
    if scenario_dir is None:
        return {}
    trace_path = scenario_dir / "trace.csv"
    if not trace_path.exists():
        return {}
    lines = trace_path.read_text(encoding="utf-8", errors="replace").splitlines()
    excerpt = "\n".join(lines[:6] + (["..."] if len(lines) > 12 else []) + lines[-6:])
    return {
        "path": _display_path(trace_path, repo_root),
        "excerpt": excerpt,
    }


def _artifact_paths(run_dir: Path, repo_root: Path) -> dict[str, Any]:
    return {
        "run_dir": _display_path(run_dir, repo_root),
        "config_path": _display_path(run_dir / "config.json", repo_root),
        "task_spec_path": _display_path(run_dir / "task_spec.json", repo_root),
        "task_summary_path": _display_path(run_dir / "task_summary.md", repo_root),
        "prompt_path": _display_path(run_dir / "prompt.txt", repo_root),
        "agent_response_path": _display_path(run_dir / "agent_response.txt", repo_root),
        "firmware_path": _display_path(run_dir / "firmware", repo_root),
        "feedback_path": _display_path(run_dir / "feedback.json", repo_root),
        "agent_feedback_path": _display_path(run_dir / "agent_feedback.json", repo_root),
        "metrics_path": _display_path(run_dir / "metrics.json", repo_root),
        "summary_path": _display_path(run_dir / "summary.md", repo_root),
        "status_path": _display_path(run_dir / "status.json", repo_root),
    }


def _commentary_for_status(status: str, integration_summary: dict[str, Any]) -> str:
    if status == PASS:
        return "All host-side checks, build steps, and QEMU scenarios passed."
    if status == HOST_TEST_FAILED:
        return "Pure logic checks failed before the firmware reached the QEMU runtime."
    if status == BUILD_FAILED:
        return "The firmware no longer builds under ESP-IDF."
    if status == FLASH_IMAGE_FAILED:
        return "The firmware built, but the flash image for QEMU could not be prepared."
    if status == QEMU_SMOKE_FAILED:
        return "The firmware built, but the smoke scenario did not complete cleanly in QEMU."
    if status == INTEGRATION_FAILED:
        failure_category = integration_summary.get("failure_category", "integration")
        return f"Closed-loop validation failed in the `{failure_category}` scenario."
    if status == EDIT_SURFACE_VIOLATION:
        return "Edits were detected outside the allowed evaluation surface."
    return "The run ended in an unknown state."


def _status_to_failure_category(status: str, integration_summary: dict[str, Any]) -> str:
    mapping = {
        HOST_TEST_FAILED: "host_tests",
        BUILD_FAILED: "build",
        FLASH_IMAGE_FAILED: "flash_image",
        QEMU_SMOKE_FAILED: "qemu_smoke",
        EDIT_SURFACE_VIOLATION: "edit_surface",
    }
    if status == INTEGRATION_FAILED:
        return str(integration_summary.get("failure_category", "integration"))
    if status == PASS:
        return "none"
    return mapping.get(status, "unknown")


def _build_feedback(
    repo_root: Path,
    run_dir: Path,
    task_spec: TaskSpec,
    feedback_config: dict[str, Any],
    stage_results: dict[str, dict[str, Any]],
    terminal_status: str,
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    integration_summary = _load_json_if_exists(run_dir / "integration" / "summary.json")
    integration_metrics = _load_json_if_exists(run_dir / "integration" / "metrics.json")
    smoke_summary = _load_json_if_exists(run_dir / "qemu_smoke" / "summary.json")

    return {
        "task": {
            "experiment_id": task_spec.experiment_id,
            "task_id": task_spec.task_id,
            "task_name": task_spec.task_name,
            "task_version": task_spec.task_version,
            "task_spec_source": _display_path(task_spec.source_path, repo_root),
        },
        "feedback_config": feedback_config,
        "stages": stage_results,
        "metrics": {
            "aggregate": integration_metrics,
            "integration": integration_summary,
            "smoke": smoke_summary.get("metrics", {}),
        },
        "uart": _collect_uart_excerpt(run_dir, repo_root),
        "traces": _collect_trace_excerpt(run_dir, repo_root),
        "artifacts": _artifact_paths(run_dir, repo_root),
        "summary": {
            "status": terminal_status,
            "task_solved": terminal_status == PASS,
            "failure_category": _status_to_failure_category(terminal_status, integration_summary),
            "commentary": _commentary_for_status(terminal_status, integration_summary),
        },
        "history": history,
    }


def _normalize_stage_payload(stage: Stage, command_result: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    return {
        "name": stage.name,
        "command": stage.command,
        "success": command_result["success"],
        "returncode": command_result["returncode"],
        "duration_s": command_result["duration_s"],
        "stdout_path": _display_path(command_result["stdout_path"], repo_root),
        "stderr_path": _display_path(command_result["stderr_path"], repo_root),
        "stdout_tail": command_result["stdout_tail"],
        "stderr_tail": command_result["stderr_tail"],
        "errors": command_result["errors"],
        "warnings": command_result["warnings"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the minimal QEMU-backed embedded evaluation pipeline.")
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=Path("artifacts/runs"),
        help="Root directory where per-run artifacts should be stored.",
    )
    parser.add_argument(
        "--allowed-edit-path",
        action="append",
        default=[],
        help="If provided, fail when git reports edits outside these paths.",
    )
    parser.add_argument(
        "--task-spec",
        type=Path,
        default=DEFAULT_TASK_SPEC,
        help="Structured task specification that drives task text, scenarios, and feedback defaults.",
    )
    parser.add_argument(
        "--feedback-mode",
        default="",
        help="Optional feedback mode override. One of: minimal, errors_only, metrics_only, logs_only, traces_only, full.",
    )
    parser.add_argument(
        "--feedback-config-json",
        default="",
        help="Optional JSON object used to override the feedback configuration from the task spec.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    task_spec = load_task_spec(args.task_spec)

    feedback_config = task_spec.feedback_config
    if args.feedback_config_json:
        feedback_config.update(json.loads(args.feedback_config_json))
    if args.feedback_mode:
        feedback_config["mode"] = args.feedback_mode
    feedback_config = normalize_feedback_config(feedback_config)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact_root = args.artifact_root if args.artifact_root.is_absolute() else repo_root / args.artifact_root
    run_dir = (artifact_root / task_spec.experiment_id / task_spec.task_id / timestamp).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    _capture_firmware_snapshot(repo_root, run_dir)
    _write_text(run_dir / "task_spec.json", json.dumps(task_spec.to_json(), indent=2, sort_keys=True) + "\n")
    task_summary = task_spec.render_agent_summary()
    _write_text(run_dir / "task_summary.md", task_summary)
    _write_text(run_dir / "prompt.txt", task_summary)
    _write_agent_response_proxy(repo_root, run_dir, args.allowed_edit_path)

    config_payload = {
        "timestamp_utc": timestamp,
        "task_spec_path": _display_path(task_spec.source_path, repo_root),
        "feedback_config": feedback_config,
        "allowed_edit_paths": args.allowed_edit_path,
        "required_scenarios": task_spec.scenario_names,
        "seeds": {
            "global_seed": 0,
            "simulator_seed": 0,
            "noise_seed": 0,
        },
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "git_commit": _git_text(repo_root, ["rev-parse", "HEAD"]),
        },
    }
    _write_text(run_dir / "config.json", json.dumps(config_payload, indent=2, sort_keys=True) + "\n")

    valid_surface, violations = _validate_edit_surface(repo_root, args.allowed_edit_path)
    stage_results: dict[str, dict[str, Any]] = {}
    terminal_status = PASS

    if not valid_surface:
        terminal_status = EDIT_SURFACE_VIOLATION
        stage_results["edit_surface"] = {
            "name": "edit_surface",
            "command": ["git", "status", "--porcelain", "--untracked-files=all"],
            "success": False,
            "returncode": 1,
            "duration_s": 0.0,
            "stdout_path": "",
            "stderr_path": "",
            "stdout_tail": "",
            "stderr_tail": "",
            "errors": violations,
            "warnings": [],
        }
    else:
        stages_to_run = [
            Stage(
                name="host_tests",
                command=["./tools/run_host_tests.sh"],
                failure_status=HOST_TEST_FAILED,
                artifact_dir_name="host_tests",
                extra_env={
                    "HOST_TEST_ARTIFACT_DIR": str(run_dir / "host_tests"),
                    "HOST_TEST_TASK_ID": task_spec.task_id,
                },
            ),
            Stage(
                name="build",
                command=["./tools/with_idf_env.sh", "idf.py", "build"],
                failure_status=BUILD_FAILED,
                artifact_dir_name="build",
                extra_env={},
            ),
            Stage(
                name="flash_image",
                command=["./tools/build_flash_image.sh"],
                failure_status=FLASH_IMAGE_FAILED,
                artifact_dir_name="flash_image",
                extra_env={"FLASH_IMAGE_ARTIFACT_DIR": str(run_dir / "flash_image")},
            ),
            Stage(
                name="qemu_smoke",
                command=[
                    "python3",
                    "tools/run_smoke.py",
                    "--artifact-dir",
                    str(run_dir / "qemu_smoke"),
                    "--port",
                    "5560",
                    "--task-spec",
                    str(task_spec.source_path),
                ],
                failure_status=QEMU_SMOKE_FAILED,
                artifact_dir_name="qemu_smoke",
                extra_env={},
            ),
            Stage(
                name="integration",
                command=[
                    "python3",
                    "tools/run_integration.py",
                    "--artifact-dir",
                    str(run_dir / "integration"),
                    "--task-spec",
                    str(task_spec.source_path),
                    *[item for scenario in task_spec.scenario_names for item in ("--scenario", scenario)],
                ],
                failure_status=INTEGRATION_FAILED,
                artifact_dir_name="integration",
                extra_env={},
            ),
        ]

        for stage in stages_to_run:
            env = os.environ.copy()
            env.update(stage.extra_env)
            command_result = _run_command(
                repo_root=repo_root,
                command=stage.command,
                env=env,
                artifact_dir=run_dir / stage.artifact_dir_name,
            )
            stage_results[stage.name] = _normalize_stage_payload(stage, command_result, repo_root)
            if not command_result["success"]:
                terminal_status = stage.failure_status
                break

    history = _collect_history(run_dir.parent, run_dir)
    feedback = _build_feedback(
        repo_root=repo_root,
        run_dir=run_dir,
        task_spec=task_spec,
        feedback_config=feedback_config,
        stage_results=stage_results,
        terminal_status=terminal_status,
        history=history,
    )
    agent_feedback = project_feedback(feedback, feedback_config)
    agent_feedback_markdown = render_feedback_markdown(agent_feedback)

    _write_text(run_dir / "feedback.json", json.dumps(feedback, indent=2, sort_keys=True) + "\n")
    _write_text(run_dir / "agent_feedback.json", json.dumps(agent_feedback, indent=2, sort_keys=True) + "\n")
    _write_text(run_dir / "agent_feedback.md", agent_feedback_markdown)
    _write_text(run_dir / "metrics.json", json.dumps(feedback.get("metrics", {}), indent=2, sort_keys=True) + "\n")
    _write_text(run_dir / "summary.md", agent_feedback_markdown)
    _write_text(
        run_dir / "status.json",
        json.dumps(
            {
                "status": terminal_status,
                "task_solved": terminal_status == PASS,
                "failure_category": feedback["summary"]["failure_category"],
                "run_dir": _display_path(run_dir, repo_root),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )

    print(json.dumps({"status": terminal_status, "run_dir": _display_path(run_dir, repo_root)}, indent=2, sort_keys=True))
    return 0 if terminal_status == PASS else 1


if __name__ == "__main__":
    sys.exit(main())
