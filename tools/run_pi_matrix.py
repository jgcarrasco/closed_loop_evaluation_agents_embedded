#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
import csv
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "artifacts" / "evaluations"
DEFAULT_WORKSPACE_ROOT = Path("/tmp") / "embedded_agent_eval_matrix"
DEFAULT_MODES = ("oneshot_blind", "realistic_self_verify", "ci_red_green", "oracle_full")
IGNORE_DIFF_PARTS = {"artifacts", "__pycache__", ".git"}
IGNORE_DIFF_SUFFIXES = {".pyc"}
IGNORE_DIFF_NAMES = {".embedded_eval_env.sh"}
RUN_EVAL_COMMAND_RE = re.compile(r"\bpython3\s+tools/run_eval\.py\b")
RUNTIME_PROBE_SOURCE_PATTERNS = (
    "FirmwareSession(",
    "FirmwareSession (",
    "from bench_public import FirmwareSession",
)
RUNTIME_PROBE_ARTIFACT_NAMES = ("transcript.log", "port_probe.log")
STAGE_FAMILY_MAP = {
    "build": "build",
    "upload": "upload",
    "run": "run",
    "host unit tests": "host_tests",
    "integration": "integration",
}
INFRA_FAILURE_PATTERNS = (
    (re.compile(r"ConnectionResetError"), "connection_reset"),
    (re.compile(r"BrokenPipeError"), "broken_pipe"),
    (re.compile(r"ConnectionRefusedError"), "connection_refused"),
    (re.compile(r"PermissionError"), "permission_error"),
    (re.compile(r"address already in use", re.IGNORECASE), "address_in_use"),
    (re.compile(r"did not become reachable"), "port_not_reachable"),
)


@dataclass(frozen=True)
class ModelSpec:
    label: str
    provider: str
    model: str
    execution_group: str


MODEL_PRESETS: dict[str, tuple[ModelSpec, ...]] = {
    "initial": (
        ModelSpec(label="gpt-5.4", provider="github-copilot", model="gpt-5.4", execution_group="remote"),
        ModelSpec(label="gpt-5.4-mini", provider="github-copilot", model="gpt-5.4-mini", execution_group="remote"),
        ModelSpec(label="qwen35-27b-q4km", provider="llama-cpp", model="qwen35-27b-q4km", execution_group="local"),
    ),
    "initial_plus_local_small": (
        ModelSpec(label="gpt-5.4", provider="github-copilot", model="gpt-5.4", execution_group="remote"),
        ModelSpec(label="gpt-5.4-mini", provider="github-copilot", model="gpt-5.4-mini", execution_group="remote"),
        ModelSpec(label="qwen35-27b-q4km", provider="llama-cpp", model="qwen35-27b-q4km", execution_group="local"),
        ModelSpec(label="qwen35-9b-ud-q6-k-xl", provider="llama-cpp-9b", model="qwen35-9b-ud-q6-k-xl", execution_group="local"),
    ),
    "local_qwen_expanded": (
        ModelSpec(label="qwen35-35b-a3b-ud-q4km", provider="llama-cpp-eval", model="qwen35-35b-a3b-ud-q4km", execution_group="local"),
        ModelSpec(label="qwen35-27b-q4km", provider="llama-cpp-eval", model="qwen35-27b-q4km", execution_group="local"),
        ModelSpec(label="qwen35-9b-ud-q4kxl", provider="llama-cpp-eval", model="qwen35-9b-ud-q4kxl", execution_group="local"),
        ModelSpec(label="qwen35-4b-ud-q4kxl", provider="llama-cpp-eval", model="qwen35-4b-ud-q4kxl", execution_group="local"),
        ModelSpec(label="qwen35-2b-ud-q4kxl", provider="llama-cpp-eval", model="qwen35-2b-ud-q4kxl", execution_group="local"),
        ModelSpec(label="qwen35-0p8b-ud-q4kxl", provider="llama-cpp-eval", model="qwen35-0p8b-ud-q4kxl", execution_group="local"),
    ),
    "paper_local_qwen": (
        ModelSpec(label="qwen35-35b-a3b-ud-q4km", provider="llama-cpp-eval", model="qwen35-35b-a3b-ud-q4km", execution_group="local"),
        ModelSpec(label="qwen35-27b-q4km", provider="llama-cpp-eval", model="qwen35-27b-q4km", execution_group="local"),
        ModelSpec(label="qwen35-9b-ud-q4kxl", provider="llama-cpp-eval", model="qwen35-9b-ud-q4kxl", execution_group="local"),
        ModelSpec(label="qwen35-4b-ud-q4kxl", provider="llama-cpp-eval", model="qwen35-4b-ud-q4kxl", execution_group="local"),
    ),
    "local_qwen_small_only": (
        ModelSpec(label="qwen35-9b-ud-q4kxl", provider="llama-cpp-eval", model="qwen35-9b-ud-q4kxl", execution_group="local"),
        ModelSpec(label="qwen35-4b-ud-q4kxl", provider="llama-cpp-eval", model="qwen35-4b-ud-q4kxl", execution_group="local"),
        ModelSpec(label="qwen35-2b-ud-q4kxl", provider="llama-cpp-eval", model="qwen35-2b-ud-q4kxl", execution_group="local"),
        ModelSpec(label="qwen35-0p8b-ud-q4kxl", provider="llama-cpp-eval", model="qwen35-0p8b-ud-q4kxl", execution_group="local"),
    ),
    "local_qwen_2b_only": (
        ModelSpec(label="qwen35-2b-ud-q4kxl", provider="llama-cpp-eval", model="qwen35-2b-ud-q4kxl", execution_group="local"),
    ),
}


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _isoformat_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _safe_slug(value: str) -> str:
    allowed = []
    for char in value:
        if char.isalnum() or char in "._-":
            allowed.append(char)
        else:
            allowed.append("-")
    slug = "".join(allowed).strip(".-")
    return slug or "unspecified"


def _discover_tasks() -> list[str]:
    task_root = REPO_ROOT / "experiments" / "tasks"
    return sorted(path.name for path in task_root.iterdir() if path.is_dir())


def _prompt_for_mode(mode: str) -> str:
    base = (
        "You are in an embedded benchmark workspace. "
        "Read START_HERE.md, docs/00_common_instructions.md, docs/10_task.md, and experiment.json. "
        "Implement the required behavior only in the allowed files. "
        "Follow the visible workflow in this workspace and stop after your final submission."
    )
    if mode == "oneshot_blind":
        return (
            base
            + " Treat this as one-shot code generation. "
            "Do not build a new local harness or spend time on repeated verification loops. "
            "Make exactly one submission with python3 tools/run_eval.py, then report the final visible submission status."
        )
    if mode == "realistic_self_verify":
        return (
            base
            + " Treat this as a realistic engineering setup. "
            "Use the visible build loop and write your own tests when the workspace exposes them. "
            "Turn each explicit acceptance bullet in docs/10_task.md into a visible test or explicit runtime probe before your first hidden submission. "
            "Include at least one firmware-level end-to-end runtime probe through UART, not just controller-only unit tests. "
            "Hidden grader results are withheld in this mode, so rely on your own verification and submit with python3 tools/run_eval.py when appropriate."
        )
    if mode == "ci_red_green":
        return (
            base
            + " Use the visible build loop and your own tests when available. "
            "Turn each explicit acceptance bullet in docs/10_task.md into a visible test or explicit runtime probe before relying on the hidden red/green signal. "
            "Include at least one firmware-level end-to-end runtime probe through UART, not just controller-only unit tests. "
            "This mode returns only hidden pass/fail, so use that red/green signal sparingly together with your own verification."
        )
    if mode == "oracle_full":
        return (
            base
            + " Use the visible build loop and your own tests when available. "
            "Turn each explicit acceptance bullet in docs/10_task.md into a visible test or explicit runtime probe before leaning on detailed hidden feedback. "
            "Include at least one firmware-level end-to-end runtime probe through UART, not just controller-only unit tests. "
            "This mode exposes detailed hidden feedback after submissions, so iterate until the task is solved or you are clearly stuck."
        )
    raise ValueError(f"unsupported mode: {mode}")


def _parse_env_file(path: Path) -> dict[str, str]:
    env_map: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("export "):
            continue
        payload = stripped[len("export ") :]
        key, _, value = payload.partition("=")
        if not key:
            continue
        env_map[key] = value.strip().strip("'").strip('"')
    return env_map


def _relative_files(root: Path) -> set[Path]:
    files: set[Path] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.name in IGNORE_DIFF_NAMES:
            continue
        if path.suffix in IGNORE_DIFF_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if any(part in IGNORE_DIFF_PARTS for part in relative.parts):
            continue
        files.add(relative)
    return files


def _read_text_if_possible(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def _diff_workspace(baseline_root: Path, workspace_root: Path) -> dict[str, Any]:
    touched: list[str] = []
    lines_added = 0
    lines_deleted = 0

    for relative in sorted(_relative_files(baseline_root) | _relative_files(workspace_root)):
        baseline_path = baseline_root / relative
        workspace_path = workspace_root / relative

        baseline_text = _read_text_if_possible(baseline_path) if baseline_path.exists() else ""
        workspace_text = _read_text_if_possible(workspace_path) if workspace_path.exists() else ""
        if baseline_text is None or workspace_text is None:
            if baseline_path.exists() != workspace_path.exists() or baseline_path.read_bytes() != workspace_path.read_bytes():
                touched.append(str(relative))
            continue
        if baseline_text == workspace_text:
            continue

        touched.append(str(relative))
        diff_lines = difflib.unified_diff(
            baseline_text.splitlines(),
            workspace_text.splitlines(),
            lineterm="",
        )
        for line in diff_lines:
            if line.startswith(("+++", "---", "@@")):
                continue
            if line.startswith("+"):
                lines_added += 1
            elif line.startswith("-"):
                lines_deleted += 1

    return {
        "files_touched": touched,
        "files_touched_count": len(touched),
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
        "lines_changed_total": lines_added + lines_deleted,
    }


def _count_self_tests(agent_tests_root: Path) -> int:
    if not agent_tests_root.exists():
        return 0
    total = 0
    for path in sorted(agent_tests_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        total += sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test"))
    return total


def _count_artifact_runs(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.iterdir() if path.is_dir() and path.name != "latest" and (path / "summary.json").exists())


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_session_file(session_dir: Path) -> Path | None:
    candidates = sorted(session_dir.glob("*.jsonl"))
    if not candidates:
        return None
    return candidates[-1]


def _tool_call_command(item: dict[str, Any]) -> str:
    arguments = item.get("arguments")
    if isinstance(arguments, dict):
        command = arguments.get("command", "")
        return command if isinstance(command, str) else ""
    return ""


def _is_hidden_submission_tool_call(item: dict[str, Any]) -> bool:
    if item.get("type") != "toolCall" or item.get("name") != "bash":
        return False
    return bool(RUN_EVAL_COMMAND_RE.search(_tool_call_command(item)))


def _parse_session_metrics(session_path: Path | None) -> dict[str, Any]:
    if session_path is None or not session_path.exists():
        return {
            "session_path": None,
            "session_started_at_utc": None,
            "first_submission_at_utc": None,
            "time_to_first_submission_seconds": None,
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
            "cache_read_tokens": None,
            "cache_write_tokens": None,
            "prompt_tokens_before_first_submission": None,
            "completion_tokens_before_first_submission": None,
            "total_tokens_before_first_submission": None,
            "prompt_tokens_after_first_submission": None,
            "completion_tokens_after_first_submission": None,
            "total_tokens_after_first_submission": None,
            "cost": None,
            "tool_call_count": 0,
            "tool_call_breakdown": {},
        }

    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    cache_read_tokens = 0
    cache_write_tokens = 0
    cost = 0.0
    tool_calls = 0
    tool_breakdown: Counter[str] = Counter()
    session_started_at: datetime | None = None
    first_submission_at: datetime | None = None
    prompt_tokens_before_first_submission = 0
    completion_tokens_before_first_submission = 0
    total_tokens_before_first_submission = 0

    for raw_line in session_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        payload = json.loads(raw_line)
        session_started_at = session_started_at or _parse_timestamp(payload.get("timestamp"))
        if payload.get("type") != "message":
            continue
        message = payload.get("message", {})
        if message.get("role") != "assistant":
            continue
        content = message.get("content", [])
        message_has_submission = any(_is_hidden_submission_tool_call(item) for item in content)

        # PI session logs may record usage either at the top level or nested inside
        # the assistant message payload, depending on the installed PI version.
        usage = payload.get("usage") or message.get("usage") or {}
        input_tokens = int(usage.get("input", 0) or 0)
        output_tokens = int(usage.get("output", 0) or 0)
        total_usage_tokens = int(usage.get("totalTokens", 0) or 0)
        cache_read = int(usage.get("cacheRead", 0) or 0)
        cache_write = int(usage.get("cacheWrite", 0) or 0)

        prompt_tokens += input_tokens
        completion_tokens += output_tokens
        total_tokens += total_usage_tokens
        cache_read_tokens += cache_read
        cache_write_tokens += cache_write
        cost += float((usage.get("cost") or {}).get("total", 0.0) or 0.0)

        if first_submission_at is None:
            prompt_tokens_before_first_submission += input_tokens
            completion_tokens_before_first_submission += output_tokens
            total_tokens_before_first_submission += total_usage_tokens

        for item in content:
            if item.get("type") != "toolCall":
                continue
            tool_calls += 1
            tool_breakdown[str(item.get("name", "unknown"))] += 1
        if message_has_submission and first_submission_at is None:
            first_submission_at = _parse_timestamp(payload.get("timestamp"))

    return {
        "session_path": str(session_path),
        "session_started_at_utc": _isoformat_utc(session_started_at),
        "first_submission_at_utc": _isoformat_utc(first_submission_at),
        "time_to_first_submission_seconds": (
            (first_submission_at - session_started_at).total_seconds()
            if session_started_at is not None and first_submission_at is not None
            else None
        ),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_write_tokens": cache_write_tokens,
        "prompt_tokens_before_first_submission": (
            prompt_tokens_before_first_submission if first_submission_at is not None else None
        ),
        "completion_tokens_before_first_submission": (
            completion_tokens_before_first_submission if first_submission_at is not None else None
        ),
        "total_tokens_before_first_submission": (
            total_tokens_before_first_submission if first_submission_at is not None else None
        ),
        "prompt_tokens_after_first_submission": (
            prompt_tokens - prompt_tokens_before_first_submission if first_submission_at is not None else None
        ),
        "completion_tokens_after_first_submission": (
            completion_tokens - completion_tokens_before_first_submission if first_submission_at is not None else None
        ),
        "total_tokens_after_first_submission": (
            total_tokens - total_tokens_before_first_submission if first_submission_at is not None else None
        ),
        "cost": cost,
        "tool_call_count": tool_calls,
        "tool_call_breakdown": dict(sorted(tool_breakdown.items())),
    }


def _stage_reached_from_hidden_summary(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    in_stages = False
    stage_reached: str | None = None
    stage_pattern = re.compile(r"^- (?P<stage>.+?): (?P<status>[A-Z_]+)")

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "Stages:":
            in_stages = True
            continue
        if not in_stages:
            continue
        if not line or line.startswith("Commentary:"):
            break
        match = stage_pattern.match(line)
        if not match:
            continue
        stage_name = match.group("stage")
        stage_status = match.group("status")
        if stage_name == "failure category":
            continue
        if stage_status != "NOT_RUN":
            stage_reached = stage_name

    return stage_reached


def _collect_new_result_dirs(task_id: str, agent_name: str, before: set[str]) -> list[Path]:
    result_root = REPO_ROOT / "experiments" / "results" / task_id / agent_name
    if not result_root.exists():
        return []
    return sorted(path for path in result_root.iterdir() if path.is_dir() and path.name not in before)


def _false_green(eval_dirs: list[Path], self_test_root: Path) -> dict[str, Any]:
    if not self_test_root.exists():
        return {
            "false_green_numerator": 0,
            "false_green_denominator": 0,
            "false_green_rate": None,
        }

    passing_self_tests = sorted(
        path.name
        for path in self_test_root.iterdir()
        if path.is_dir()
        and path.name != "latest"
        and (path / "summary.json").exists()
        and _load_json(path / "summary.json").get("success")
    )
    numerator = 0
    denominator = 0

    for eval_dir in eval_dirs:
        had_green = any(self_test_timestamp <= eval_dir.name for self_test_timestamp in passing_self_tests)
        if not had_green:
            continue
        denominator += 1
        evaluation = _load_json(eval_dir / "evaluation.json")
        if evaluation.get("hidden_status", {}).get("status") != "PASS":
            numerator += 1

    return {
        "false_green_numerator": numerator,
        "false_green_denominator": denominator,
        "false_green_rate": (numerator / denominator) if denominator else None,
    }


def _runtime_probe_metrics(agent_tests_root: Path, self_test_root: Path) -> dict[str, Any]:
    runtime_probe_files: list[str] = []
    if agent_tests_root.exists():
        for path in sorted(agent_tests_root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if any(pattern in text for pattern in RUNTIME_PROBE_SOURCE_PATTERNS):
                runtime_probe_files.append(str(path.relative_to(agent_tests_root.parent)))

    runtime_probe_run_dirs = 0
    runtime_probe_case_dirs: set[str] = set()
    if self_test_root.exists():
        for run_dir in sorted(self_test_root.iterdir()):
            if not run_dir.is_dir() or run_dir.name == "latest" or not (run_dir / "summary.json").exists():
                continue
            case_root = run_dir / "cases"
            case_dirs_in_run: set[Path] = set()
            if case_root.exists():
                for artifact_name in RUNTIME_PROBE_ARTIFACT_NAMES:
                    case_dirs_in_run.update(path.parent for path in case_root.rglob(artifact_name))
            if case_dirs_in_run:
                runtime_probe_run_dirs += 1
                runtime_probe_case_dirs.update(str(path.relative_to(run_dir)) for path in case_dirs_in_run)

    return {
        "runtime_probe_present": bool(runtime_probe_files) or bool(runtime_probe_case_dirs),
        "runtime_probe_files": runtime_probe_files,
        "runtime_probe_runs": runtime_probe_run_dirs,
        "runtime_probe_case_count": len(runtime_probe_case_dirs),
        "runtime_probe_executed": bool(runtime_probe_case_dirs),
    }


def _infra_failure_details(hidden_summary_path: Path | None) -> dict[str, Any]:
    if hidden_summary_path is None or not hidden_summary_path.exists():
        return {
            "infra_failure": False,
            "infra_failure_reason": None,
        }

    summary_text = hidden_summary_path.read_text(encoding="utf-8", errors="replace")
    for pattern, reason in INFRA_FAILURE_PATTERNS:
        if pattern.search(summary_text):
            return {
                "infra_failure": True,
                "infra_failure_reason": reason,
            }

    return {
        "infra_failure": False,
        "infra_failure_reason": None,
    }


def _failure_family(status: str | None, stage_reached: str | None, failure_category: str | None, *, infra_failure: bool) -> str:
    if status == "PASS":
        return "pass"
    if infra_failure:
        return "infra"
    if status == "NO_SUBMISSION":
        return "no_submission"
    if stage_reached:
        mapped = STAGE_FAMILY_MAP.get(stage_reached.lower())
        if mapped:
            return mapped
    return _safe_slug(failure_category or status or "unknown")


def _final_hidden_outcome(eval_dirs: list[Path]) -> dict[str, Any]:
    if not eval_dirs:
        return {
            "status": "NO_SUBMISSION",
            "pass_fail": False,
            "stage_reached": None,
            "failure_category": "no_submission",
            "evaluation_dir": None,
            "hidden_summary_path": None,
            "failure_family": "no_submission",
            "infra_failure": False,
            "infra_failure_reason": None,
        }

    final_dir = eval_dirs[-1]
    evaluation = _load_json(final_dir / "evaluation.json")
    hidden_summary_path = final_dir / "hidden_summary.md"
    hidden_status = evaluation.get("hidden_status", {})
    stage_reached = _stage_reached_from_hidden_summary(hidden_summary_path)
    failure_category = hidden_status.get("failure_category")
    infra_details = _infra_failure_details(hidden_summary_path)

    return {
        "status": hidden_status.get("status"),
        "pass_fail": bool(hidden_status.get("task_solved", False)),
        "stage_reached": stage_reached,
        "failure_category": failure_category,
        "evaluation_dir": str(final_dir),
        "hidden_summary_path": str(hidden_summary_path) if hidden_summary_path.exists() else None,
        "failure_family": _failure_family(
            hidden_status.get("status"),
            stage_reached,
            failure_category,
            infra_failure=infra_details["infra_failure"],
        ),
        **infra_details,
    }


def _write_aggregate(outputs: list[dict[str, Any]], output_root: Path) -> None:
    summary_json_path = output_root / "summary.json"
    summary_csv_path = output_root / "summary.csv"
    summary_md_path = output_root / "summary.md"
    aggregate_metrics_path = output_root / "aggregate_metrics.json"

    summary_json_path.write_text(json.dumps(outputs, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    fieldnames = [
        "task_id",
        "mode",
        "model_label",
        "provider",
        "model",
        "hidden_status",
        "pass_fail",
        "failure_family",
        "stage_reached",
        "failure_category",
        "infra_failure",
        "infra_failure_reason",
        "wall_clock_seconds",
        "time_to_first_submission_seconds",
        "iterations",
        "hidden_eval_calls",
        "build_attempts",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        "prompt_tokens_before_first_submission",
        "completion_tokens_before_first_submission",
        "total_tokens_before_first_submission",
        "prompt_tokens_after_first_submission",
        "completion_tokens_after_first_submission",
        "total_tokens_after_first_submission",
        "cost",
        "tool_call_count",
        "files_touched_count",
        "lines_changed_total",
        "self_tests_written",
        "self_test_runs",
        "runtime_probe_present",
        "runtime_probe_executed",
        "runtime_probe_runs",
        "runtime_probe_case_count",
        "false_green_numerator",
        "false_green_denominator",
        "false_green_rate",
        "run_dir",
    ]

    with summary_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for output in outputs:
            writer.writerow(
                {
                    "task_id": output["task_id"],
                    "mode": output["mode"],
                    "model_label": output["model"]["label"],
                    "provider": output["model"]["provider"],
                    "model": output["model"]["model"],
                    "hidden_status": output["final_hidden_outcome"]["status"],
                    "pass_fail": output["final_hidden_outcome"]["pass_fail"],
                    "failure_family": output["final_hidden_outcome"]["failure_family"],
                    "stage_reached": output["final_hidden_outcome"]["stage_reached"],
                    "failure_category": output["final_hidden_outcome"]["failure_category"],
                    "infra_failure": output["final_hidden_outcome"]["infra_failure"],
                    "infra_failure_reason": output["final_hidden_outcome"]["infra_failure_reason"],
                    "wall_clock_seconds": output["efficiency"]["wall_clock_seconds"],
                    "time_to_first_submission_seconds": output["efficiency"]["time_to_first_submission_seconds"],
                    "iterations": output["efficiency"]["iterations"],
                    "hidden_eval_calls": output["efficiency"]["hidden_eval_calls"],
                    "build_attempts": output["efficiency"]["build_attempts"],
                    "prompt_tokens": output["model_usage"]["prompt_tokens"],
                    "completion_tokens": output["model_usage"]["completion_tokens"],
                    "total_tokens": output["model_usage"]["total_tokens"],
                    "cache_read_tokens": output["model_usage"]["cache_read_tokens"],
                    "cache_write_tokens": output["model_usage"]["cache_write_tokens"],
                    "prompt_tokens_before_first_submission": output["model_usage"]["prompt_tokens_before_first_submission"],
                    "completion_tokens_before_first_submission": output["model_usage"]["completion_tokens_before_first_submission"],
                    "total_tokens_before_first_submission": output["model_usage"]["total_tokens_before_first_submission"],
                    "prompt_tokens_after_first_submission": output["model_usage"]["prompt_tokens_after_first_submission"],
                    "completion_tokens_after_first_submission": output["model_usage"]["completion_tokens_after_first_submission"],
                    "total_tokens_after_first_submission": output["model_usage"]["total_tokens_after_first_submission"],
                    "cost": output["model_usage"]["cost"],
                    "tool_call_count": output["tool_behavior"]["tool_call_count"],
                    "files_touched_count": output["tool_behavior"]["files_touched_count"],
                    "lines_changed_total": output["tool_behavior"]["lines_changed_total"],
                    "self_tests_written": output["testing_behavior"]["self_tests_written"],
                    "self_test_runs": output["testing_behavior"]["self_test_runs"],
                    "runtime_probe_present": output["testing_behavior"]["runtime_probe_present"],
                    "runtime_probe_executed": output["testing_behavior"]["runtime_probe_executed"],
                    "runtime_probe_runs": output["testing_behavior"]["runtime_probe_runs"],
                    "runtime_probe_case_count": output["testing_behavior"]["runtime_probe_case_count"],
                    "false_green_numerator": output["testing_behavior"]["false_green_numerator"],
                    "false_green_denominator": output["testing_behavior"]["false_green_denominator"],
                    "false_green_rate": output["testing_behavior"]["false_green_rate"],
                    "run_dir": output["run_dir"],
                }
            )

    failure_family_histogram = Counter(output["final_hidden_outcome"]["failure_family"] for output in outputs)
    failure_family_histogram_by_mode = {
        mode: dict(
            sorted(Counter(output["final_hidden_outcome"]["failure_family"] for output in outputs if output["mode"] == mode).items())
        )
        for mode in sorted({output["mode"] for output in outputs})
    }
    failure_family_histogram_by_model = {
        model_label: dict(
            sorted(
                Counter(
                    output["final_hidden_outcome"]["failure_family"]
                    for output in outputs
                    if output["model"]["label"] == model_label
                ).items()
            )
        )
        for model_label in sorted({output["model"]["label"] for output in outputs})
    }
    aggregate_metrics = {
        "run_count": len(outputs),
        "pass_count": sum(1 for output in outputs if output["final_hidden_outcome"]["pass_fail"]),
        "infra_failure_count": sum(1 for output in outputs if output["final_hidden_outcome"]["infra_failure"]),
        "failure_family_histogram": dict(sorted(failure_family_histogram.items())),
        "failure_family_histogram_by_mode": failure_family_histogram_by_mode,
        "failure_family_histogram_by_model": failure_family_histogram_by_model,
    }
    aggregate_metrics_path.write_text(json.dumps(aggregate_metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# PI Benchmark Sweep",
        "",
        "| Task | Mode | Model | Hidden Outcome | Family | Stage | Time (s) | First Submit (s) | Hidden Evals | Builds | Self-Tests | Probe | Tokens |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for output in outputs:
        lines.append(
            "| {task} | {mode} | {model} | {status} | {family} | {stage} | {wall:.1f} | {first_submit} | {evals} | {builds} | {tests} | {probe} | {tokens} |".format(
                task=output["task_id"],
                mode=output["mode"],
                model=output["model"]["label"],
                status=output["final_hidden_outcome"]["status"],
                family=output["final_hidden_outcome"]["failure_family"],
                stage=output["final_hidden_outcome"]["stage_reached"] or "-",
                wall=float(output["efficiency"]["wall_clock_seconds"]),
                first_submit=(
                    f"{float(output['efficiency']['time_to_first_submission_seconds']):.1f}"
                    if output["efficiency"]["time_to_first_submission_seconds"] is not None
                    else "-"
                ),
                evals=int(output["efficiency"]["hidden_eval_calls"]),
                builds=int(output["efficiency"]["build_attempts"]),
                tests=int(output["testing_behavior"]["self_test_runs"]),
                probe="yes" if output["testing_behavior"]["runtime_probe_executed"] else ("authored" if output["testing_behavior"]["runtime_probe_present"] else "no"),
                tokens=output["model_usage"]["total_tokens"] or 0,
            )
        )
    summary_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _prepare_workspace(
    task_id: str,
    agent_name: str,
    workspace: Path,
    mode: str,
) -> dict[str, str]:
    command = [
        str(REPO_ROOT / "tools" / "prepare_agent_eval.sh"),
        task_id,
        agent_name,
        "--workspace",
        str(workspace),
        "--benchmark-mode",
        mode,
        "--public-task-contract",
        "prose_only",
    ]
    completed = subprocess.run(command, cwd=REPO_ROOT, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "workspace preparation failed")

    env_path = workspace / ".embedded_eval_env.sh"
    if not env_path.exists():
        raise RuntimeError(f"missing evaluator environment file: {env_path}")
    return _parse_env_file(env_path)


def _cleanup_run_temp(task_id: str, agent_name: str, workspace: Path) -> None:
    cleanup_paths = [workspace.parent]
    for root_name in ("embedded_eval_hidden_harness", "embedded_eval_hidden_runs"):
        task_root = Path("/tmp") / root_name / task_id
        if not task_root.exists():
            continue
        cleanup_paths.extend(sorted(task_root.glob(f"{agent_name}_*")))

    for path in cleanup_paths:
        shutil.rmtree(path, ignore_errors=True)


def _runner_exception_record(
    *,
    task_id: str,
    mode: str,
    model_spec: ModelSpec,
    agent_name: str,
    run_dir: Path,
    workspace: Path,
    baseline_root: Path,
    prompt_path: Path,
    stdout_path: Path,
    stderr_path: Path,
    wall_clock: float,
    error_message: str,
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "mode": mode,
        "model": asdict(model_spec),
        "agent_name": agent_name,
        "run_dir": str(run_dir),
        "workspace": str(workspace),
        "baseline_workspace": str(baseline_root),
        "pi_command": None,
        "pi_returncode": None,
        "pi_timed_out": False,
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        "prompt_path": str(prompt_path),
        "session_copy": None,
        "evaluation_dirs": [],
        "runner_exception": error_message,
        "final_hidden_outcome": {
            "status": "INFRA_FAILURE",
            "pass_fail": False,
            "stage_reached": None,
            "failure_category": "runner_exception",
            "evaluation_dir": None,
            "hidden_summary_path": None,
            "failure_family": "infra",
            "infra_failure": True,
            "infra_failure_reason": "runner_exception",
        },
        "efficiency": {
            "wall_clock_seconds": wall_clock,
            "iterations": 0,
            "hidden_eval_calls": 0,
            "build_attempts": 0,
            "first_submission_at_utc": None,
            "time_to_first_submission_seconds": None,
        },
        "model_usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "prompt_tokens_before_first_submission": 0,
            "completion_tokens_before_first_submission": 0,
            "total_tokens_before_first_submission": 0,
            "prompt_tokens_after_first_submission": 0,
            "completion_tokens_after_first_submission": 0,
            "total_tokens_after_first_submission": 0,
            "cost": 0.0,
        },
        "tool_behavior": {
            "tool_call_count": 0,
            "tool_call_breakdown": {},
            "files_touched_count": 0,
            "files_touched": [],
            "lines_added": 0,
            "lines_deleted": 0,
            "lines_changed_total": 0,
        },
        "testing_behavior": {
            "self_tests_written": 0,
            "self_test_runs": 0,
            "runtime_probe_present": False,
            "runtime_probe_files": [],
            "runtime_probe_runs": 0,
            "runtime_probe_case_count": 0,
            "runtime_probe_executed": False,
            "false_green_numerator": 0,
            "false_green_denominator": 0,
            "false_green_rate": None,
        },
    }


def _copy_session(run_dir: Path, session_path: Path | None) -> str | None:
    if session_path is None or not session_path.exists():
        return None
    destination = run_dir / "session.jsonl"
    shutil.copy2(session_path, destination)
    return str(destination)


def _run_single(
    task_id: str,
    mode: str,
    model_spec: ModelSpec,
    output_root: Path,
    workspace_root: Path,
    timeout_sec: int,
    skip_existing: bool,
    cleanup_temp: bool,
    sweep_id: str,
) -> dict[str, Any]:
    run_slug = f"{_safe_slug(task_id)}__{_safe_slug(mode)}__{_safe_slug(model_spec.label)}"
    run_dir = output_root / "runs" / run_slug
    summary_path = run_dir / "summary.json"
    if skip_existing and summary_path.exists():
        return _load_json(summary_path)

    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    workspace = workspace_root / sweep_id / run_slug / "workspace"
    if workspace.parent.exists():
        shutil.rmtree(workspace.parent)
    workspace.parent.mkdir(parents=True, exist_ok=True)

    agent_name = _safe_slug(f"pi-{task_id}-{mode}-{model_spec.label}-{sweep_id}")
    baseline_root = workspace.parent / "baseline"
    prompt = _prompt_for_mode(mode)
    prompt_path = run_dir / "prompt.txt"
    prompt_path.write_text(prompt + "\n", encoding="utf-8")
    stdout_path = run_dir / "pi_stdout.log"
    stderr_path = run_dir / "pi_stderr.log"
    record: dict[str, Any] | None = None
    start = time.monotonic()

    try:
        existing_result_dirs = {
            path.name
            for path in (REPO_ROOT / "experiments" / "results" / task_id / agent_name).glob("*")
            if path.is_dir()
        }

        env_map = _prepare_workspace(task_id, agent_name, workspace, mode)

        if baseline_root.exists():
            shutil.rmtree(baseline_root)
        shutil.copytree(workspace, baseline_root)

        session_dir = run_dir / "pi_session_dir"
        session_dir.mkdir(parents=True, exist_ok=True)

        command = [
            "pi",
            "--provider",
            model_spec.provider,
            "--model",
            model_spec.model,
            "--tools",
            "read,bash,edit,write,grep,find,ls",
            "--no-extensions",
            "--no-skills",
            "--no-prompt-templates",
            "--no-themes",
            "--session-dir",
            str(session_dir),
            "-p",
            prompt,
        ]

        env = os.environ.copy()
        env.update(env_map)
        env["EMBEDDED_EVAL_FRAMEWORK"] = "pi"
        env["EMBEDDED_EVAL_PROVIDER"] = model_spec.provider
        env["EMBEDDED_EVAL_MODEL"] = model_spec.model
        env["EMBEDDED_EVAL_NOTES"] = f"pi matrix sweep {sweep_id}"

        timed_out = False
        returncode: int | None = None
        with stdout_path.open("w", encoding="utf-8") as stdout_handle, stderr_path.open("w", encoding="utf-8") as stderr_handle:
            try:
                completed = subprocess.run(
                    command,
                    cwd=workspace,
                    env=env,
                    check=False,
                    stdout=stdout_handle,
                    stderr=stderr_handle,
                    timeout=timeout_sec,
                    text=True,
                )
                returncode = completed.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
        wall_clock = time.monotonic() - start

        session_path = _latest_session_file(session_dir)
        copied_session_path = _copy_session(run_dir, session_path)

        new_eval_dirs = _collect_new_result_dirs(task_id, agent_name, existing_result_dirs)
        final_hidden_outcome = _final_hidden_outcome(new_eval_dirs)

        build_root = workspace / "artifacts" / "public" / "builds"
        self_test_root = workspace / "artifacts" / "public" / "self_tests"
        build_attempts = _count_artifact_runs(build_root)
        self_test_runs = _count_artifact_runs(self_test_root)
        hidden_eval_calls = len(new_eval_dirs)
        iterations = max(build_attempts, self_test_runs, hidden_eval_calls)

        session_metrics = _parse_session_metrics(session_path)
        diff_metrics = _diff_workspace(baseline_root, workspace)
        false_green_metrics = _false_green(new_eval_dirs, self_test_root)
        runtime_probe_metrics = _runtime_probe_metrics(workspace / "agent_tests", self_test_root)

        record = {
            "task_id": task_id,
            "mode": mode,
            "model": asdict(model_spec),
            "agent_name": agent_name,
            "run_dir": str(run_dir),
            "workspace": str(workspace),
            "baseline_workspace": str(baseline_root),
            "pi_command": command,
            "pi_returncode": returncode,
            "pi_timed_out": timed_out,
            "stdout_log": str(stdout_path),
            "stderr_log": str(stderr_path),
            "prompt_path": str(prompt_path),
            "session_copy": copied_session_path,
            "evaluation_dirs": [str(path) for path in new_eval_dirs],
            "runner_exception": None,
            "final_hidden_outcome": final_hidden_outcome,
            "efficiency": {
                "wall_clock_seconds": wall_clock,
                "iterations": iterations,
                "hidden_eval_calls": hidden_eval_calls,
                "build_attempts": build_attempts,
                "first_submission_at_utc": session_metrics["first_submission_at_utc"],
                "time_to_first_submission_seconds": session_metrics["time_to_first_submission_seconds"],
            },
            "model_usage": {
                "prompt_tokens": session_metrics["prompt_tokens"],
                "completion_tokens": session_metrics["completion_tokens"],
                "total_tokens": session_metrics["total_tokens"],
                "cache_read_tokens": session_metrics["cache_read_tokens"],
                "cache_write_tokens": session_metrics["cache_write_tokens"],
                "prompt_tokens_before_first_submission": session_metrics["prompt_tokens_before_first_submission"],
                "completion_tokens_before_first_submission": session_metrics["completion_tokens_before_first_submission"],
                "total_tokens_before_first_submission": session_metrics["total_tokens_before_first_submission"],
                "prompt_tokens_after_first_submission": session_metrics["prompt_tokens_after_first_submission"],
                "completion_tokens_after_first_submission": session_metrics["completion_tokens_after_first_submission"],
                "total_tokens_after_first_submission": session_metrics["total_tokens_after_first_submission"],
                "cost": session_metrics["cost"],
            },
            "tool_behavior": {
                "tool_call_count": session_metrics["tool_call_count"],
                "tool_call_breakdown": session_metrics["tool_call_breakdown"],
                "files_touched_count": diff_metrics["files_touched_count"],
                "files_touched": diff_metrics["files_touched"],
                "lines_added": diff_metrics["lines_added"],
                "lines_deleted": diff_metrics["lines_deleted"],
                "lines_changed_total": diff_metrics["lines_changed_total"],
            },
            "testing_behavior": {
                "self_tests_written": _count_self_tests(workspace / "agent_tests"),
                "self_test_runs": self_test_runs,
                **runtime_probe_metrics,
                **false_green_metrics,
            },
        }
    except Exception as exc:
        wall_clock = time.monotonic() - start
        error_message = f"{type(exc).__name__}: {exc}"
        (run_dir / "runner_exception.txt").write_text(error_message + "\n", encoding="utf-8")
        record = _runner_exception_record(
            task_id=task_id,
            mode=mode,
            model_spec=model_spec,
            agent_name=agent_name,
            run_dir=run_dir,
            workspace=workspace,
            baseline_root=baseline_root,
            prompt_path=prompt_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            wall_clock=wall_clock,
            error_message=error_message,
        )

    summary_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if cleanup_temp:
        _cleanup_run_temp(task_id, agent_name, workspace)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a reproducible PI evaluation matrix across tasks, benchmark modes, and models.")
    parser.add_argument("--model-preset", default="initial", choices=sorted(MODEL_PRESETS))
    parser.add_argument("--tasks", nargs="*", default=None, help="Optional task ids. Defaults to all tasks.")
    parser.add_argument("--modes", nargs="*", default=list(DEFAULT_MODES), choices=list(DEFAULT_MODES))
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--workspace-root", type=Path, default=DEFAULT_WORKSPACE_ROOT)
    parser.add_argument("--timeout-sec", type=int, default=3600)
    parser.add_argument("--parallel-remote", type=int, default=1)
    parser.add_argument("--parallel-local", type=int, default=1)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--cleanup-temp", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.parallel_remote != 1 or args.parallel_local != 1:
        raise SystemExit(
            "parallel PI sweeps are disabled because the hidden evaluator still uses fixed QEMU/UART ports; "
            "keep --parallel-remote=1 and --parallel-local=1 until per-run port allocation exists"
        )

    tasks = args.tasks or _discover_tasks()
    models = MODEL_PRESETS[args.model_preset]
    sweep_id = _utc_timestamp()
    output_root = (args.output_root or (DEFAULT_OUTPUT_ROOT / f"pi_matrix_{sweep_id}")).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    manifest = {
        "sweep_id": sweep_id,
        "created_at_utc": sweep_id,
        "tasks": tasks,
        "modes": args.modes,
        "models": [asdict(model) for model in models],
        "run_order": "model_then_task_then_mode",
        "timeout_sec": args.timeout_sec,
        "parallel_limits": {
            "remote": args.parallel_remote,
            "local": args.parallel_local,
        },
        "workspace_root": str(args.workspace_root.resolve()),
        "prompt_by_mode": {mode: _prompt_for_mode(mode) for mode in args.modes},
    }
    (output_root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    combinations = [(task, mode, model) for model in models for task in tasks for mode in args.modes]
    print(f"[pi-matrix] output root: {output_root}")
    print(f"[pi-matrix] runs: {len(combinations)}")
    for task, mode, model in combinations:
        print(f"[pi-matrix] queued {task} | {mode} | {model.label}")

    if args.dry_run:
        return 0

    results: list[dict[str, Any]] = []
    for index, (task_id, mode, model_spec) in enumerate(combinations, start=1):
        print(f"[pi-matrix] ({index}/{len(combinations)}) starting {task_id} | {mode} | {model_spec.label}", flush=True)
        record = _run_single(
            task_id=task_id,
            mode=mode,
            model_spec=model_spec,
            output_root=output_root,
            workspace_root=args.workspace_root.resolve(),
            timeout_sec=args.timeout_sec,
            skip_existing=args.skip_existing,
            cleanup_temp=args.cleanup_temp,
            sweep_id=sweep_id,
        )
        results.append(record)
        _write_aggregate(results, output_root)
        outcome = record["final_hidden_outcome"]
        print(
            "[pi-matrix] completed {task} | {mode} | {model} -> {status} ({stage})".format(
                task=task_id,
                mode=mode,
                model=model_spec.label,
                status=outcome["status"],
                stage=outcome["stage_reached"] or "no-stage",
            ),
            flush=True,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
