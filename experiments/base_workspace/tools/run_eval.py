from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))


VISIBLE_RUN_ROOT = WORKSPACE_ROOT / "artifacts" / "runs"
EXPERIMENT_PATH = WORKSPACE_ROOT / "experiment.json"
VISIBLE_EDIT_SURFACE_VIOLATION = "VISIBLE_EDIT_SURFACE_VIOLATION"
EVALUATOR_BRIDGE_FAILED = "EVALUATOR_BRIDGE_FAILED"
SUBMISSION_BUDGET_EXHAUSTED = "SUBMISSION_BUDGET_EXHAUSTED"
SUBMISSION_RECORDED = "SUBMISSION_RECORDED"
VISIBLE_PASS = "PASS"
VISIBLE_FAIL = "FAIL"
DEFAULT_LOCAL_PATHS = ["agent_tests"]

BENCHMARK_MODE_DEFAULTS: dict[str, dict[str, Any]] = {
    "oneshot_blind": {
        "submission_feedback": "none",
        "max_submissions": 1,
    },
    "realistic_self_verify": {
        "submission_feedback": "none",
        "max_submissions": None,
    },
    "ci_red_green": {
        "submission_feedback": "red_green",
        "max_submissions": None,
    },
    "oracle_full": {
        "submission_feedback": "oracle_full",
        "max_submissions": None,
    },
}


def _required_env_path(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"{name} is not set. This workspace was launched without the hidden evaluator configured. "
            "That is an operator setup issue; the agent should be started with EMBEDDED_EVAL_* already set."
        )
    return Path(value).resolve()


def _load_experiment() -> dict[str, object]:
    return json.loads(EXPERIMENT_PATH.read_text(encoding="utf-8"))


def _normalize_benchmark_config(raw_config: dict[str, Any] | None) -> dict[str, Any]:
    config = dict(raw_config or {})
    mode = str(config.get("mode", "realistic_self_verify")).strip() or "realistic_self_verify"
    if mode not in BENCHMARK_MODE_DEFAULTS:
        available = ", ".join(sorted(BENCHMARK_MODE_DEFAULTS))
        raise RuntimeError(f"unknown benchmark mode: {mode}. available modes: {available}")

    merged = dict(BENCHMARK_MODE_DEFAULTS[mode])
    merged.update(config)
    merged["mode"] = mode

    max_submissions = merged.get("max_submissions")
    if max_submissions in {"", None}:
        merged["max_submissions"] = None
    else:
        merged["max_submissions"] = int(max_submissions)
        if merged["max_submissions"] <= 0:
            raise RuntimeError("benchmark.max_submissions must be positive when provided")

    submission_feedback = str(merged.get("submission_feedback", "")).strip()
    if submission_feedback not in {"none", "red_green", "oracle_full"}:
        raise RuntimeError(
            "benchmark.submission_feedback must be one of: none, red_green, oracle_full"
        )

    return merged


def _local_paths(experiment: dict[str, object]) -> list[str]:
    raw_paths = experiment.get("local_paths", DEFAULT_LOCAL_PATHS)
    return [str(path) for path in raw_paths]


def _manifest_task_spec_path(hidden_root: Path, task_id: str) -> str:
    manifest_path = hidden_root / "experiments" / "tasks" / task_id / "task.json"
    if not manifest_path.exists():
        return ""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    candidate = str(manifest.get("task_spec_path", "")).strip()
    return candidate if candidate else ""


def _resolve_hidden_task_spec_path(hidden_root: Path, experiment: dict[str, object]) -> str:
    candidates = []
    source_task_spec_path = str(experiment.get("source_task_spec_path", "")).strip()
    task_spec_path = str(experiment.get("task_spec_path", "")).strip()
    if source_task_spec_path:
        candidates.append(source_task_spec_path)
    if task_spec_path:
        candidates.append(task_spec_path)
    task_id = str(experiment.get("task_id", "")).strip()
    if task_id:
        manifest_task_spec_path = _manifest_task_spec_path(hidden_root, task_id)
        if manifest_task_spec_path:
            candidates.append(manifest_task_spec_path)
        candidates.append(f"specs/{task_id}.json")

    for candidate in candidates:
        if (hidden_root / candidate).exists():
            return candidate

    return candidates[0] if candidates else ""


def _changed_paths(repo_root: Path) -> list[str]:
    probe = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return []
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line[3:] for line in completed.stdout.splitlines() if line]


def _validate_visible_edit_surface(
    repo_root: Path,
    editable_paths: list[str],
    local_paths: list[str],
) -> list[str]:
    allowed_paths = list(editable_paths) + list(local_paths)
    violations = []
    for path in _changed_paths(repo_root):
        if path.startswith("artifacts/"):
            continue
        if any(path == allowed or path.startswith(f"{allowed}/") for allowed in allowed_paths):
            continue
        violations.append(path)
    return violations


def _existing_run_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        str(status_path.parent.relative_to(path))
        for status_path in path.rglob("status.json")
        if status_path.parent.is_dir()
    }


def _pick_hidden_run_dir(path: Path, previous_runs: set[str]) -> Path:
    current_runs = sorted(status_path.parent for status_path in path.rglob("status.json"))
    new_runs = [child for child in current_runs if str(child.relative_to(path)) not in previous_runs]
    if new_runs:
        return new_runs[-1]
    if current_runs:
        return current_runs[-1]
    raise RuntimeError(f"no run directories found under {path}")


def _copy_sync_files_to_hidden(hidden_root: Path, sync_paths: list[str]) -> None:
    for relative in sync_paths:
        source = WORKSPACE_ROOT / relative
        target = hidden_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _refresh_latest(visible_run_dir: Path) -> None:
    latest_dir = WORKSPACE_ROOT / "artifacts" / "latest"
    if latest_dir.exists() or latest_dir.is_symlink():
        if latest_dir.is_symlink() or latest_dir.is_file():
            latest_dir.unlink()
        else:
            shutil.rmtree(latest_dir)
    shutil.copytree(visible_run_dir, latest_dir)


def _copy_if_exists(source: Path, target: Path) -> None:
    if not source.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _hidden_status(hidden_run_dir: Path) -> dict[str, Any]:
    return _load_json_if_exists(hidden_run_dir / "status.json")


def _visible_submission_count() -> int:
    if not VISIBLE_RUN_ROOT.exists():
        return 0
    return sum(1 for _ in VISIBLE_RUN_ROOT.rglob("status.json"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_feedback_markdown(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_oracle_feedback(hidden_run_dir: Path, visible_run_dir: Path) -> dict[str, Any]:
    hidden_status = _hidden_status(hidden_run_dir)
    visible_status = {
        "status": hidden_status.get("status"),
        "task_solved": hidden_status.get("task_solved", False),
        "failure_category": hidden_status.get("failure_category", ""),
    }
    _write_json(visible_run_dir / "status.json", visible_status)
    _copy_if_exists(hidden_run_dir / "agent_feedback.json", visible_run_dir / "feedback.json")
    _copy_if_exists(hidden_run_dir / "agent_feedback.md", visible_run_dir / "feedback.md")
    _copy_if_exists(hidden_run_dir / "metrics.json", visible_run_dir / "metrics.json")

    if not (visible_run_dir / "feedback.md").exists():
        fallback = hidden_run_dir / "feedback.json"
        if fallback.exists():
            _write_feedback_markdown(
                visible_run_dir / "feedback.md",
                [json.dumps(json.loads(fallback.read_text(encoding="utf-8")), indent=2, sort_keys=True)],
            )
    return visible_status


def _none_feedback_commentary(benchmark_config: dict[str, Any]) -> list[str]:
    lines = ["Submission recorded. Hidden grader results are withheld in this benchmark mode."]
    if benchmark_config["mode"] == "oneshot_blind":
        lines.append("This workspace intentionally omits the public self-verification helpers for this run.")
    else:
        lines.append("Use the visible build and self-test tools for local iteration.")
    return lines


def _write_none_feedback(
    visible_run_dir: Path,
    *,
    benchmark_config: dict[str, Any],
    submission_index: int,
) -> dict[str, Any]:
    commentary_lines = _none_feedback_commentary(benchmark_config)
    visible_status = {
        "status": SUBMISSION_RECORDED,
        "benchmark_mode": benchmark_config["mode"],
        "submission_index": submission_index,
        "submission_budget": benchmark_config.get("max_submissions"),
    }
    _write_json(visible_run_dir / "status.json", visible_status)
    _write_json(
        visible_run_dir / "feedback.json",
        {
            "status": SUBMISSION_RECORDED,
            "benchmark_mode": benchmark_config["mode"],
            "submission_index": submission_index,
            "submission_budget": benchmark_config.get("max_submissions"),
            "commentary": " ".join(commentary_lines),
        },
    )
    _write_feedback_markdown(
        visible_run_dir / "feedback.md",
        [
            f"Status: {SUBMISSION_RECORDED}",
            "",
            f"Benchmark mode: {benchmark_config['mode']}",
            f"Submission index: {submission_index}",
            f"Submission budget: {benchmark_config.get('max_submissions') or 'unlimited'}",
            "",
            "Commentary:",
            *commentary_lines,
        ],
    )
    return visible_status


def _write_red_green_feedback(
    hidden_run_dir: Path,
    visible_run_dir: Path,
    *,
    benchmark_config: dict[str, Any],
    submission_index: int,
) -> dict[str, Any]:
    hidden_status = _hidden_status(hidden_run_dir)
    task_solved = bool(hidden_status.get("task_solved", False))
    visible_status = {
        "status": VISIBLE_PASS if task_solved else VISIBLE_FAIL,
        "task_solved": task_solved,
        "benchmark_mode": benchmark_config["mode"],
        "submission_index": submission_index,
        "submission_budget": benchmark_config.get("max_submissions"),
    }
    _write_json(visible_run_dir / "status.json", visible_status)
    _write_json(
        visible_run_dir / "feedback.json",
        {
            "status": visible_status["status"],
            "task_solved": task_solved,
            "benchmark_mode": benchmark_config["mode"],
            "submission_index": submission_index,
            "submission_budget": benchmark_config.get("max_submissions"),
            "commentary": "Hidden grader result exposed as red/green only.",
        },
    )
    _write_feedback_markdown(
        visible_run_dir / "feedback.md",
        [
            f"Status: {visible_status['status']}",
            "",
            f"Benchmark mode: {benchmark_config['mode']}",
            f"Submission index: {submission_index}",
            f"Submission budget: {benchmark_config.get('max_submissions') or 'unlimited'}",
            "",
            "Commentary:",
            "Hidden grader result exposed as red/green only.",
        ],
    )
    return visible_status


def _write_feedback(
    hidden_run_dir: Path,
    visible_run_dir: Path,
    *,
    benchmark_config: dict[str, Any],
    submission_index: int,
) -> dict[str, Any]:
    submission_feedback = benchmark_config["submission_feedback"]
    if submission_feedback == "oracle_full":
        visible_status = _write_oracle_feedback(hidden_run_dir, visible_run_dir)
    elif submission_feedback == "red_green":
        visible_status = _write_red_green_feedback(
            hidden_run_dir,
            visible_run_dir,
            benchmark_config=benchmark_config,
            submission_index=submission_index,
        )
    else:
        visible_status = _write_none_feedback(
            visible_run_dir,
            benchmark_config=benchmark_config,
            submission_index=submission_index,
        )

    _refresh_latest(visible_run_dir)
    return visible_status


def _write_local_violation_feedback(visible_run_dir: Path, violations: list[str]) -> dict[str, Any]:
    visible_status = {
        "status": VISIBLE_EDIT_SURFACE_VIOLATION,
        "violations": violations,
    }
    _write_json(visible_run_dir / "status.json", visible_status)
    _write_json(visible_run_dir / "feedback.json", {"status": VISIBLE_EDIT_SURFACE_VIOLATION, "violations": violations})
    feedback_lines = [
        f"Status: {VISIBLE_EDIT_SURFACE_VIOLATION}",
        "",
        "Guidance:",
        "- You changed files outside the allowed task surface.",
        "- Revert edits outside the editable controller files or local test paths and try again.",
        "",
        "Visible edit-surface violations:",
    ]
    feedback_lines.extend(f"- {violation}" for violation in violations)
    _write_feedback_markdown(visible_run_dir / "feedback.md", feedback_lines)

    _refresh_latest(visible_run_dir)
    return visible_status


def _write_submission_budget_feedback(
    visible_run_dir: Path,
    *,
    benchmark_config: dict[str, Any],
    submission_index: int,
) -> dict[str, Any]:
    visible_status = {
        "status": SUBMISSION_BUDGET_EXHAUSTED,
        "benchmark_mode": benchmark_config["mode"],
        "submission_index": submission_index,
        "submission_budget": benchmark_config.get("max_submissions"),
    }
    _write_json(visible_run_dir / "status.json", visible_status)
    _write_json(
        visible_run_dir / "feedback.json",
        {
            "status": SUBMISSION_BUDGET_EXHAUSTED,
            "benchmark_mode": benchmark_config["mode"],
            "submission_index": submission_index,
            "submission_budget": benchmark_config.get("max_submissions"),
            "commentary": "The submission budget for this workspace has been exhausted.",
        },
    )
    _write_feedback_markdown(
        visible_run_dir / "feedback.md",
        [
            f"Status: {SUBMISSION_BUDGET_EXHAUSTED}",
            "",
            f"Benchmark mode: {benchmark_config['mode']}",
            f"Submission index: {submission_index}",
            f"Submission budget: {benchmark_config.get('max_submissions') or 'unlimited'}",
            "",
            "Commentary:",
            "The submission budget for this workspace has been exhausted.",
        ],
    )
    _refresh_latest(visible_run_dir)
    return visible_status


def _write_bridge_failure_feedback(visible_run_dir: Path) -> dict[str, Any]:
    visible_status = {
        "status": EVALUATOR_BRIDGE_FAILED,
        "task_solved": False,
        "failure_category": "evaluator_bridge",
    }
    _write_json(visible_run_dir / "status.json", visible_status)
    _write_json(
        visible_run_dir / "feedback.json",
        {
            "status": EVALUATOR_BRIDGE_FAILED,
            "commentary": (
                "The hidden evaluator did not produce visible feedback. "
                "This is a tooling or operator problem rather than a task-logic result."
            ),
        },
    )
    _write_feedback_markdown(
        visible_run_dir / "feedback.md",
        [
            f"Status: {EVALUATOR_BRIDGE_FAILED}",
            "",
            "Commentary:",
            "The hidden evaluator did not produce visible feedback.",
            "This is a tooling or operator problem rather than a task-logic result.",
        ],
    )
    _refresh_latest(visible_run_dir)
    return visible_status


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    slug = slug.strip(".-")
    return slug or "unspecified"


def _evaluation_context_from_env() -> dict[str, object]:
    number_fields = {
        "prompt_tokens": "EMBEDDED_EVAL_PROMPT_TOKENS",
        "completion_tokens": "EMBEDDED_EVAL_COMPLETION_TOKENS",
        "total_tokens": "EMBEDDED_EVAL_TOTAL_TOKENS",
        "cost_usd": "EMBEDDED_EVAL_COST_USD",
    }
    string_fields = {
        "framework": "EMBEDDED_EVAL_FRAMEWORK",
        "provider": "EMBEDDED_EVAL_PROVIDER",
        "model": "EMBEDDED_EVAL_MODEL",
        "run_id": "EMBEDDED_EVAL_FRAMEWORK_RUN_ID",
        "benchmark_mode_override": "EMBEDDED_EVAL_BENCHMARK_MODE",
    }

    payload: dict[str, object] = {}
    for key, env_name in string_fields.items():
        value = os.environ.get(env_name, "").strip()
        if value:
            payload[key] = value
    for key, env_name in number_fields.items():
        value = os.environ.get(env_name, "").strip()
        if not value:
            continue
        try:
            payload[key] = int(value)
        except ValueError:
            try:
                payload[key] = float(value)
            except ValueError:
                payload[key] = value
    return payload


def _record_result(
    results_root: Path,
    experiment: dict[str, object],
    resolved_task_spec_path: str,
    benchmark_config: dict[str, Any],
    agent_name: str,
    run_label: str,
    notes: str,
    hidden_run_dir: Path | None,
    visible_run_dir: Path,
    visible_status: dict[str, object],
    submission_index: int,
) -> Path:
    timestamp = visible_run_dir.name
    task_id = str(experiment["task_id"])
    result_dir = results_root / task_id / _safe_slug(agent_name) / timestamp
    result_dir.mkdir(parents=True, exist_ok=True)

    visible_copy_dir = result_dir / "visible_run"
    if visible_copy_dir.exists():
        shutil.rmtree(visible_copy_dir)
    shutil.copytree(visible_run_dir, visible_copy_dir)

    hidden_status = {}
    if hidden_run_dir is not None:
        _copy_if_exists(hidden_run_dir / "summary.md", result_dir / "hidden_summary.md")
        _copy_if_exists(hidden_run_dir / "status.json", result_dir / "hidden_status.json")
        _copy_if_exists(hidden_run_dir / "feedback.json", result_dir / "hidden_feedback.json")
        _copy_if_exists(hidden_run_dir / "agent_feedback.json", result_dir / "hidden_agent_feedback.json")
        _copy_if_exists(hidden_run_dir / "metrics.json", result_dir / "hidden_metrics.json")
        hidden_status = _hidden_status(hidden_run_dir)

    evaluation_context = _evaluation_context_from_env()
    record = {
        "timestamp": timestamp,
        "task_id": task_id,
        "task_name": experiment["task_name"],
        "task_version": experiment["task_version"],
        "task_spec_path": resolved_task_spec_path,
        "feedback": experiment.get("feedback", {}),
        "benchmark": benchmark_config,
        "agent_name": agent_name,
        "run_label": run_label,
        "notes": notes,
        "visible_status": visible_status,
        "status": visible_status["status"],
        "hidden_status": hidden_status,
        "editable_paths": experiment["editable_paths"],
        "sync_paths": experiment.get("sync_paths", experiment["editable_paths"]),
        "local_paths": _local_paths(experiment),
        "submission_index": submission_index,
        "submission_budget": benchmark_config.get("max_submissions"),
        "visible_run_dir": str(visible_run_dir),
        "hidden_run_dir": str(hidden_run_dir) if hidden_run_dir is not None else "",
        "evaluation_context": evaluation_context,
    }
    record.update(evaluation_context)
    _write_json(result_dir / "evaluation.json", record)

    return result_dir


def _strict_exit_code(visible_status: dict[str, object]) -> int:
    status = str(visible_status.get("status", ""))
    if visible_status.get("task_solved", False):
        return 0
    return 0 if status == SUBMISSION_RECORDED else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit the current visible workspace to the hidden evaluator.")
    parser.add_argument(
        "--agent-name",
        default=os.environ.get("EMBEDDED_EVAL_AGENT_NAME", "unspecified-agent"),
        help="Human-readable agent name used when recording results.",
    )
    parser.add_argument(
        "--run-label",
        default=os.environ.get("EMBEDDED_EVAL_RUN_LABEL", ""),
        help="Optional operator-supplied label for this run series.",
    )
    parser.add_argument(
        "--notes",
        default=os.environ.get("EMBEDDED_EVAL_NOTES", ""),
        help="Optional free-form notes stored with the run record.",
    )
    parser.add_argument(
        "--strict-exit-code",
        action="store_true",
        help="Return a non-zero exit code when the visible submission status is a failure.",
    )
    args = parser.parse_args()

    experiment = _load_experiment()
    benchmark_config = _normalize_benchmark_config(experiment.get("benchmark", {}))
    editable_paths = [str(path) for path in experiment["editable_paths"]]
    sync_paths = [str(path) for path in experiment.get("sync_paths", editable_paths)]
    local_paths = _local_paths(experiment)

    hidden_root = _required_env_path("EMBEDDED_EVAL_HARNESS_ROOT")
    hidden_run_root = _required_env_path("EMBEDDED_EVAL_RUN_ROOT")
    results_root = Path(
        os.environ.get("EMBEDDED_EVAL_RESULTS_ROOT", str(hidden_root / "experiments" / "results"))
    ).resolve()
    task_spec_path = _resolve_hidden_task_spec_path(hidden_root, experiment)

    visible_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    visible_run_dir = VISIBLE_RUN_ROOT / visible_timestamp
    visible_run_dir.mkdir(parents=True, exist_ok=True)
    hidden_run_root.mkdir(parents=True, exist_ok=True)
    results_root.mkdir(parents=True, exist_ok=True)

    submission_index = _visible_submission_count() + 1
    max_submissions = benchmark_config.get("max_submissions")
    if max_submissions is not None and submission_index > int(max_submissions):
        visible_status = _write_submission_budget_feedback(
            visible_run_dir,
            benchmark_config=benchmark_config,
            submission_index=submission_index,
        )
        _record_result(
            results_root=results_root,
            experiment=experiment,
            resolved_task_spec_path=task_spec_path,
            benchmark_config=benchmark_config,
            agent_name=args.agent_name,
            run_label=args.run_label,
            notes=args.notes,
            hidden_run_dir=None,
            visible_run_dir=visible_run_dir,
            visible_status=visible_status,
            submission_index=submission_index,
        )
        print((visible_run_dir / "feedback.md").read_text(encoding="utf-8"))
        return _strict_exit_code(visible_status) if args.strict_exit_code else 0

    violations = _validate_visible_edit_surface(WORKSPACE_ROOT, editable_paths, local_paths)
    if violations:
        visible_status = _write_local_violation_feedback(visible_run_dir, violations)
        _record_result(
            results_root=results_root,
            experiment=experiment,
            resolved_task_spec_path=task_spec_path,
            benchmark_config=benchmark_config,
            agent_name=args.agent_name,
            run_label=args.run_label,
            notes=args.notes,
            hidden_run_dir=None,
            visible_run_dir=visible_run_dir,
            visible_status=visible_status,
            submission_index=submission_index,
        )
        print((visible_run_dir / "feedback.md").read_text(encoding="utf-8"))
        return _strict_exit_code(visible_status) if args.strict_exit_code else 0

    _copy_sync_files_to_hidden(hidden_root, sync_paths)
    previous_hidden_runs = _existing_run_keys(hidden_run_root)

    command = ["python3", "tools/agent_loop.py", "--artifact-root", str(hidden_run_root)]
    for editable_path in editable_paths:
        command.extend(["--allowed-edit-path", editable_path])

    if task_spec_path:
        command.extend(["--task-spec", task_spec_path])

    feedback_config = experiment.get("feedback", {})
    if feedback_config:
        command.extend(["--feedback-config-json", json.dumps(feedback_config, sort_keys=True)])

    subprocess.run(command, cwd=hidden_root, check=False, capture_output=True, text=True)

    try:
        hidden_run_dir = _pick_hidden_run_dir(hidden_run_root, previous_hidden_runs)
    except RuntimeError:
        visible_status = _write_bridge_failure_feedback(visible_run_dir)
        _record_result(
            results_root=results_root,
            experiment=experiment,
            resolved_task_spec_path=task_spec_path,
            benchmark_config=benchmark_config,
            agent_name=args.agent_name,
            run_label=args.run_label,
            notes=args.notes,
            hidden_run_dir=None,
            visible_run_dir=visible_run_dir,
            visible_status=visible_status,
            submission_index=submission_index,
        )
        print((visible_run_dir / "feedback.md").read_text(encoding="utf-8"))
        return _strict_exit_code(visible_status) if args.strict_exit_code else 0

    visible_status = _write_feedback(
        hidden_run_dir,
        visible_run_dir,
        benchmark_config=benchmark_config,
        submission_index=submission_index,
    )
    _record_result(
        results_root=results_root,
        experiment=experiment,
        resolved_task_spec_path=task_spec_path,
        benchmark_config=benchmark_config,
        agent_name=args.agent_name,
        run_label=args.run_label,
        notes=args.notes,
        hidden_run_dir=hidden_run_dir,
        visible_run_dir=visible_run_dir,
        visible_status=visible_status,
        submission_index=submission_index,
    )

    print((visible_run_dir / "feedback.md").read_text(encoding="utf-8"))
    return _strict_exit_code(visible_status) if args.strict_exit_code else 0


if __name__ == "__main__":
    raise SystemExit(main())
