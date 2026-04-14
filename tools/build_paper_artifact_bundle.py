#!/usr/bin/env python3
"""Build a paper-facing bundle for the authoritative 420-run evaluation set.

The paper uses three official repetitions of 140 unique runs each:
  - original paper sweep (`rep0`)
  - campaign repeat 1 (`rep1`)
  - campaign repeat 2 (`rep2`)

Some raw sweep roots contain extra qwen3.5-27B diagnostic runs that are not part
of the official paper accounting. This script keeps those raw roots intact but
generates a curated index and manifest that make the official 420-run set easy
to inspect.
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_DIR = REPO_ROOT / "artifacts" / "evaluations" / "paper_closed_loop_eval_420"


MODEL_LABELS = {
    "gpt-5.4": "gpt-5.4",
    "gpt-5.4-mini": "gpt-5.4-mini",
    "qwen35-27b-q4km": "qwen3.5-27B",
    "qwen35-35b-a3b-ud-q4km": "qwen3.5-35B-A3B",
    "qwen35-9b-ud-q4kxl": "qwen3.5-9B",
    "qwen35-4b-ud-q4kxl": "qwen3.5-4B",
    "qwen35-2b-ud-q4kxl": "qwen3.5-2B",
}

MODEL_ORDER = [
    "gpt-5.4",
    "gpt-5.4-mini",
    "qwen35-27b-q4km",
    "qwen35-35b-a3b-ud-q4km",
    "qwen35-9b-ud-q4kxl",
    "qwen35-4b-ud-q4kxl",
    "qwen35-2b-ud-q4kxl",
]

TASK_ORDER = [
    "filter_tank_sequence",
    "mixing_tank_fill_heat",
    "pressure_vessel_interlock",
    "tank_fill_drain",
    "thermal_chamber_hysteresis",
]

MODE_ORDER = [
    "oneshot_blind",
    "realistic_self_verify",
    "ci_red_green",
    "oracle_full",
]

SUMMARY_FIELDNAMES = [
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


@dataclass(frozen=True)
class SourceRoot:
    name: str
    relative_root: str
    repetition: str
    description: str
    official_models: tuple[str, ...]
    diagnostic_only_models: tuple[str, ...] = ()


SOURCE_ROOTS = [
    SourceRoot(
        name="rep0_mixed",
        relative_root="artifacts/evaluations/pi_matrix_20260324T125039Z",
        repetition="rep0",
        description="Original mixed-model sweep used for the main paper table.",
        official_models=("gpt-5.4", "gpt-5.4-mini", "qwen35-27b-q4km"),
    ),
    SourceRoot(
        name="rep0_local_35b",
        relative_root="artifacts/evaluations/pi_matrix_local_qwen_20260325T110603Z",
        repetition="rep0",
        description="Original local Qwen sweep; only the 35B-A3B rows are official paper runs here.",
        official_models=("qwen35-35b-a3b-ud-q4km",),
        diagnostic_only_models=("qwen35-27b-q4km",),
    ),
    SourceRoot(
        name="rep0_local_small",
        relative_root="artifacts/evaluations/pi_matrix_local_qwen_small_20260325T174111Z",
        repetition="rep0",
        description="Original small local Qwen sweep (9B, 4B, 2B).",
        official_models=("qwen35-9b-ud-q4kxl", "qwen35-4b-ud-q4kxl", "qwen35-2b-ud-q4kxl"),
    ),
    SourceRoot(
        name="rep1_mixed",
        relative_root="artifacts/evaluations/pi_matrix_paper_mixed_20260327_campaign_rep1",
        repetition="rep1",
        description="Campaign repeat 1 mixed-model sweep; qwen3.5-27B rows are diagnostic duplicates here.",
        official_models=("gpt-5.4", "gpt-5.4-mini"),
        diagnostic_only_models=("qwen35-27b-q4km",),
    ),
    SourceRoot(
        name="rep1_local",
        relative_root="artifacts/evaluations/pi_matrix_paper_local_20260327_campaign_rep1",
        repetition="rep1",
        description="Campaign repeat 1 local sweep for qwen3.5-27B/35B-A3B/9B/4B.",
        official_models=("qwen35-27b-q4km", "qwen35-35b-a3b-ud-q4km", "qwen35-9b-ud-q4kxl", "qwen35-4b-ud-q4kxl"),
    ),
    SourceRoot(
        name="rep1_2b",
        relative_root="artifacts/evaluations/pi_matrix_paper_2b_20260327_campaign_rep1",
        repetition="rep1",
        description="Campaign repeat 1 qwen3.5-2B-only sweep.",
        official_models=("qwen35-2b-ud-q4kxl",),
    ),
    SourceRoot(
        name="rep2_mixed",
        relative_root="artifacts/evaluations/pi_matrix_paper_mixed_20260327_campaign_rep2",
        repetition="rep2",
        description="Campaign repeat 2 mixed-model sweep; qwen3.5-27B rows are diagnostic duplicates here.",
        official_models=("gpt-5.4", "gpt-5.4-mini"),
        diagnostic_only_models=("qwen35-27b-q4km",),
    ),
    SourceRoot(
        name="rep2_local",
        relative_root="artifacts/evaluations/pi_matrix_paper_local_20260327_campaign_rep2",
        repetition="rep2",
        description="Campaign repeat 2 local sweep for qwen3.5-27B/35B-A3B/9B/4B.",
        official_models=("qwen35-27b-q4km", "qwen35-35b-a3b-ud-q4km", "qwen35-9b-ud-q4kxl", "qwen35-4b-ud-q4kxl"),
    ),
    SourceRoot(
        name="rep2_2b",
        relative_root="artifacts/evaluations/pi_matrix_paper_2b_20260327_campaign_rep2",
        repetition="rep2",
        description="Campaign repeat 2 qwen3.5-2B-only sweep.",
        official_models=("qwen35-2b-ud-q4kxl",),
    ),
]


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def git_head() -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True)
        .strip()
    )


def order_index(values: list[str], value: str) -> int:
    try:
        return values.index(value)
    except ValueError:
        return len(values)


def bundle_run_name(repetition: str, task_id: str, mode: str, model_label: str) -> str:
    return f"{repetition}__{task_id}__{mode}__{model_label}"


def summary_row_from_data(data: dict, bundle_run_dir: str) -> dict:
    return {
        "task_id": data["task_id"],
        "mode": data["mode"],
        "model_label": data["model"]["label"],
        "provider": data["model"]["provider"],
        "model": data["model"]["model"],
        "hidden_status": data["final_hidden_outcome"]["status"] or "",
        "pass_fail": bool(data["final_hidden_outcome"]["pass_fail"]),
        "failure_family": data["final_hidden_outcome"]["failure_family"] or "",
        "stage_reached": data["final_hidden_outcome"]["stage_reached"] or "",
        "failure_category": data["final_hidden_outcome"]["failure_category"] or "",
        "infra_failure": bool(data["final_hidden_outcome"].get("infra_failure")),
        "infra_failure_reason": data["final_hidden_outcome"].get("infra_failure_reason") or "",
        "wall_clock_seconds": data["efficiency"]["wall_clock_seconds"],
        "time_to_first_submission_seconds": data["efficiency"]["time_to_first_submission_seconds"],
        "iterations": data["efficiency"]["iterations"],
        "hidden_eval_calls": data["efficiency"]["hidden_eval_calls"],
        "build_attempts": data["efficiency"]["build_attempts"],
        "prompt_tokens": data["model_usage"]["prompt_tokens"],
        "completion_tokens": data["model_usage"]["completion_tokens"],
        "total_tokens": data["model_usage"]["total_tokens"],
        "cache_read_tokens": data["model_usage"]["cache_read_tokens"],
        "cache_write_tokens": data["model_usage"]["cache_write_tokens"],
        "prompt_tokens_before_first_submission": data["model_usage"]["prompt_tokens_before_first_submission"],
        "completion_tokens_before_first_submission": data["model_usage"]["completion_tokens_before_first_submission"],
        "total_tokens_before_first_submission": data["model_usage"]["total_tokens_before_first_submission"],
        "prompt_tokens_after_first_submission": data["model_usage"]["prompt_tokens_after_first_submission"],
        "completion_tokens_after_first_submission": data["model_usage"]["completion_tokens_after_first_submission"],
        "total_tokens_after_first_submission": data["model_usage"]["total_tokens_after_first_submission"],
        "cost": data["model_usage"]["cost"],
        "tool_call_count": data["tool_behavior"]["tool_call_count"],
        "files_touched_count": data["tool_behavior"]["files_touched_count"],
        "lines_changed_total": data["tool_behavior"]["lines_changed_total"],
        "self_tests_written": data["testing_behavior"]["self_tests_written"],
        "self_test_runs": data["testing_behavior"]["self_test_runs"],
        "runtime_probe_present": data["testing_behavior"]["runtime_probe_present"],
        "runtime_probe_executed": data["testing_behavior"]["runtime_probe_executed"],
        "runtime_probe_runs": data["testing_behavior"]["runtime_probe_runs"],
        "runtime_probe_case_count": data["testing_behavior"]["runtime_probe_case_count"],
        "false_green_numerator": data["testing_behavior"]["false_green_numerator"],
        "false_green_denominator": data["testing_behavior"]["false_green_denominator"],
        "false_green_rate": data["testing_behavior"]["false_green_rate"],
        "run_dir": bundle_run_dir,
    }


def adjusted_summary_json(data: dict, row: dict) -> dict:
    adjusted = json.loads(json.dumps(data))
    adjusted["repetition"] = row["repetition"]
    adjusted["run_dir"] = row["run_dir"]
    adjusted["prompt_path"] = row["prompt_txt"]
    adjusted["session_copy"] = row["session_jsonl"]
    adjusted["stdout_log"] = row["stdout_log"]
    adjusted["stderr_log"] = row["stderr_log"]
    if adjusted.get("pi_command"):
        for idx, token in enumerate(adjusted["pi_command"]):
            if token == "--session-dir" and idx + 1 < len(adjusted["pi_command"]):
                adjusted["pi_command"][idx + 1] = f"{row['run_dir']}/pi_session_dir"
                break
    return adjusted


def outcome_family(row: dict) -> str:
    if row["pass_fail"]:
        return "pass"
    return row["failure_family"] or "unknown"


def probe_label(summary_row: dict) -> str:
    if summary_row["runtime_probe_executed"]:
        return "yes"
    if summary_row["runtime_probe_present"]:
        return "authored"
    return "no"


def display_status(summary_row: dict) -> str:
    return summary_row["hidden_status"] or "None"


def display_stage(summary_row: dict) -> str:
    return summary_row["stage_reached"] or "-"


def display_first_submit(summary_row: dict) -> str:
    value = summary_row["time_to_first_submission_seconds"]
    return "-" if value in ("", None) else f"{value:.1f}"


def row_sort_key(row: dict) -> tuple[int, int, int, int]:
    return (
        order_index(["rep0", "rep1", "rep2"], row["repetition"]),
        order_index(TASK_ORDER, row["task_id"]),
        order_index(MODE_ORDER, row["mode"]),
        order_index(MODEL_ORDER, row["model_label"]),
    )


def load_rows() -> tuple[list[dict], list[dict], list[dict]]:
    raw_rows: list[dict] = []
    official_rows: list[dict] = []
    excluded_rows: list[dict] = []

    for source in SOURCE_ROOTS:
        root = REPO_ROOT / source.relative_root
        for summary_path in sorted((root / "runs").glob("*/summary.json")):
            data = json.loads(summary_path.read_text())
            model_label = data["model"]["label"]
            run_name = bundle_run_name(source.repetition, data["task_id"], data["mode"], model_label)
            bundle_run_dir = f"{rel(BUNDLE_DIR)}/runs/{run_name}"
            row = {
                "source_name": source.name,
                "source_root": source.relative_root,
                "repetition": source.repetition,
                "task_id": data["task_id"],
                "mode": data["mode"],
                "model_label": model_label,
                "model_name": MODEL_LABELS[model_label],
                "provider": data["model"]["provider"],
                "hidden_status": data["final_hidden_outcome"]["status"] or "",
                "pass_fail": bool(data["final_hidden_outcome"]["pass_fail"]),
                "failure_family": data["final_hidden_outcome"]["failure_family"] or "",
                "stage_reached": data["final_hidden_outcome"]["stage_reached"] or "",
                "failure_category": data["final_hidden_outcome"]["failure_category"] or "",
                "infra_failure": bool(data["final_hidden_outcome"].get("infra_failure")),
                "infra_failure_reason": data["final_hidden_outcome"].get("infra_failure_reason") or "",
                "wall_clock_seconds": data["efficiency"]["wall_clock_seconds"],
                "time_to_first_submission_seconds": data["efficiency"]["time_to_first_submission_seconds"],
                "iterations": data["efficiency"]["iterations"],
                "hidden_eval_calls": data["efficiency"]["hidden_eval_calls"],
                "build_attempts": data["efficiency"]["build_attempts"],
                "total_tokens": data["model_usage"]["total_tokens"],
                "tool_call_count": data["tool_behavior"]["tool_call_count"],
                "files_touched_count": data["tool_behavior"]["files_touched_count"],
                "lines_changed_total": data["tool_behavior"]["lines_changed_total"],
                "self_tests_written": data["testing_behavior"]["self_tests_written"],
                "self_test_runs": data["testing_behavior"]["self_test_runs"],
                "bundle_run_name": run_name,
                "run_dir": bundle_run_dir,
                "summary_json": f"{bundle_run_dir}/summary.json",
                "prompt_txt": f"{bundle_run_dir}/prompt.txt",
                "session_jsonl": f"{bundle_run_dir}/session.jsonl",
                "stdout_log": f"{bundle_run_dir}/pi_stdout.log",
                "stderr_log": f"{bundle_run_dir}/pi_stderr.log",
                "original_run_dir": rel(Path(data["run_dir"])),
                "original_summary_json": rel(summary_path),
                "summary_row": summary_row_from_data(data, bundle_run_dir),
                "adjusted_summary": adjusted_summary_json(data, {
                    "source_name": source.name,
                    "source_root": source.relative_root,
                    "repetition": source.repetition,
                    "original_run_dir": rel(Path(data["run_dir"])),
                    "run_dir": bundle_run_dir,
                    "prompt_txt": f"{bundle_run_dir}/prompt.txt",
                    "session_jsonl": f"{bundle_run_dir}/session.jsonl",
                    "stdout_log": f"{bundle_run_dir}/pi_stdout.log",
                    "stderr_log": f"{bundle_run_dir}/pi_stderr.log",
                }),
            }
            raw_rows.append(row)
            if model_label in source.official_models:
                official_rows.append(row)
            else:
                row = dict(row)
                row["exclusion_reason"] = exclusion_reason(source.name, model_label)
                excluded_rows.append(row)

    return raw_rows, official_rows, excluded_rows


def exclusion_reason(source_name: str, model_label: str) -> str:
    if source_name in {"rep1_mixed", "rep2_mixed"} and model_label == "qwen35-27b-q4km":
        return "Duplicate qwen3.5-27B mixed-sweep rerun; official paper accounting reuses the local-sweep qwen3.5-27B runs for that repetition."
    if source_name == "rep0_local_35b" and model_label == "qwen35-27b-q4km":
        return "Partial extra qwen3.5-27B runs in the original local root; the official rep0 qwen3.5-27B results come from pi_matrix_20260324T125039Z."
    return "Excluded from official paper accounting."


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fieldnames} for row in rows])


def rate(numer: int, denom: int) -> str:
    return f"{(100.0 * numer / denom):.1f}" if denom else ""


def build_summaries(official_rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    by_model: Counter[str] = Counter()
    by_model_total: Counter[str] = Counter()
    by_model_mode: Counter[tuple[str, str]] = Counter()
    by_model_mode_total: Counter[tuple[str, str]] = Counter()
    by_root: Counter[str] = Counter()
    by_root_total: Counter[str] = Counter()

    for row in official_rows:
        key_model = row["model_name"]
        key_model_mode = (row["model_name"], row["mode"])
        by_model_total[key_model] += 1
        by_model[key_model] += int(row["pass_fail"])
        by_model_mode_total[key_model_mode] += 1
        by_model_mode[key_model_mode] += int(row["pass_fail"])
        by_root_total[row["source_name"]] += 1
        by_root[row["source_name"]] += int(row["pass_fail"])

    summary_by_model = []
    for model_name in sorted(by_model_total):
        total = by_model_total[model_name]
        passes = by_model[model_name]
        summary_by_model.append(
            {
                "model_name": model_name,
                "pass_count": passes,
                "run_count": total,
                "pass_rate_pct": rate(passes, total),
            }
        )

    summary_by_model_mode = []
    for model_name, mode in sorted(by_model_mode_total):
        total = by_model_mode_total[(model_name, mode)]
        passes = by_model_mode[(model_name, mode)]
        summary_by_model_mode.append(
            {
                "model_name": model_name,
                "mode": mode,
                "pass_count": passes,
                "run_count": total,
                "pass_rate_pct": rate(passes, total),
            }
        )

    summary_by_root = []
    source_map = {source.name: source for source in SOURCE_ROOTS}
    for source_name in [source.name for source in SOURCE_ROOTS]:
        total = by_root_total[source_name]
        passes = by_root[source_name]
        summary_by_root.append(
            {
                "source_name": source_name,
                "repetition": source_map[source_name].repetition,
                "source_root": source_map[source_name].relative_root,
                "pass_count": passes,
                "run_count": total,
                "pass_rate_pct": rate(passes, total),
            }
        )

    return summary_by_model, summary_by_model_mode, summary_by_root


def write_manifest(raw_rows: list[dict], official_rows: list[dict], excluded_rows: list[dict]) -> None:
    del raw_rows, official_rows, excluded_rows


def write_readme(raw_rows: list[dict], official_rows: list[dict], excluded_rows: list[dict]) -> None:
    del raw_rows, excluded_rows
    lines = [
        "# Paper Closed-Loop Evaluation Bundle",
        "",
        "This directory contains the official `420`-run artifact bundle used in the paper manuscript.",
        "",
        "## Included Files",
        "",
        f"- `runs/`: `420` per-run directories under `{rel(BUNDLE_DIR)}/runs/`.",
        "- `summary.csv`, `summary.json`, `summary.md`, `aggregate_metrics.json`: top-level summaries for the full bundle.",
        "- `official_run_index.csv`: one row per run with task, mode, model, outcome, and direct paths to the copied artifacts.",
        "- `official_summary_by_model.csv` and `official_summary_by_model_mode.csv`: pooled pass summaries.",
        "",
        "## Per-Run Artifacts",
        "",
        "Each run directory contains:",
        "",
        "- `prompt.txt`",
        "- `session.jsonl`",
        "- `pi_stdout.log`",
        "- `pi_stderr.log`",
        "- `summary.json`",
    ]

    (BUNDLE_DIR / "README.md").write_text("\n".join(lines) + "\n")


def copy_curated_runs(official_rows: list[dict]) -> None:
    runs_dir = BUNDLE_DIR / "runs"
    if runs_dir.exists():
        shutil.rmtree(runs_dir)
    runs_dir.mkdir(parents=True, exist_ok=True)

    for row in official_rows:
        source_dir = REPO_ROOT / row["original_run_dir"]
        target_dir = runs_dir / row["bundle_run_name"]
        shutil.copytree(source_dir, target_dir)


def write_curated_summary_files(official_rows: list[dict]) -> None:
    sorted_rows = sorted(official_rows, key=row_sort_key)
    summary_rows = [row["summary_row"] for row in sorted_rows]
    write_csv(BUNDLE_DIR / "summary.csv", summary_rows, SUMMARY_FIELDNAMES)
    (BUNDLE_DIR / "summary.json").write_text(
        json.dumps([row["adjusted_summary"] for row in sorted_rows], indent=2) + "\n"
    )

    lines = [
        "# PI Benchmark Sweep",
        "",
        "| Task | Mode | Model | Hidden Outcome | Family | Stage | Time (s) | First Submit (s) | Hidden Evals | Builds | Self-Tests | Probe | Tokens |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in summary_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["task_id"],
                    row["mode"],
                    row["model_label"],
                    display_status(row),
                    row["failure_family"] or "pass",
                    display_stage(row),
                    f"{row['wall_clock_seconds']:.1f}",
                    display_first_submit(row),
                    str(row["hidden_eval_calls"]),
                    str(row["build_attempts"]),
                    str(row["self_test_runs"]),
                    probe_label(row),
                    str(row["total_tokens"]),
                ]
            )
            + " |"
        )
    (BUNDLE_DIR / "summary.md").write_text("\n".join(lines) + "\n")

    failure_hist = Counter(outcome_family(row) for row in summary_rows)
    by_mode: dict[str, Counter[str]] = defaultdict(Counter)
    by_model: dict[str, Counter[str]] = defaultdict(Counter)
    for row in summary_rows:
        family = outcome_family(row)
        by_mode[row["mode"]][family] += 1
        by_model[row["model_label"]][family] += 1

    aggregate_metrics = {
        "failure_family_histogram": dict(failure_hist),
        "failure_family_histogram_by_mode": {mode: dict(counts) for mode, counts in sorted(by_mode.items())},
        "failure_family_histogram_by_model": {model: dict(counts) for model, counts in sorted(by_model.items())},
        "infra_failure_count": sum(int(row["infra_failure"]) for row in summary_rows),
        "pass_count": sum(int(row["pass_fail"]) for row in summary_rows),
        "run_count": len(summary_rows),
    }
    (BUNDLE_DIR / "aggregate_metrics.json").write_text(json.dumps(aggregate_metrics, indent=2) + "\n")


def main() -> None:
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    raw_rows, official_rows, excluded_rows = load_rows()

    if len(official_rows) != 420:
        raise RuntimeError(f"Expected 420 official runs, found {len(official_rows)}")

    if len(excluded_rows) != 42:
        raise RuntimeError(f"Expected 42 excluded diagnostic runs, found {len(excluded_rows)}")

    official_fieldnames = [
        "repetition",
        "task_id",
        "mode",
        "model_label",
        "model_name",
        "provider",
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
        "total_tokens",
        "tool_call_count",
        "files_touched_count",
        "lines_changed_total",
        "self_tests_written",
        "self_test_runs",
        "run_dir",
        "summary_json",
        "prompt_txt",
        "session_jsonl",
        "stdout_log",
        "stderr_log",
    ]
    write_csv(BUNDLE_DIR / "official_run_index.csv", official_rows, official_fieldnames)
    summary_by_model, summary_by_model_mode, _ = build_summaries(official_rows)
    write_csv(
        BUNDLE_DIR / "official_summary_by_model.csv",
        summary_by_model,
        ["model_name", "pass_count", "run_count", "pass_rate_pct"],
    )
    write_csv(
        BUNDLE_DIR / "official_summary_by_model_mode.csv",
        summary_by_model_mode,
        ["model_name", "mode", "pass_count", "run_count", "pass_rate_pct"],
    )

    copy_curated_runs(official_rows)
    write_curated_summary_files(official_rows)
    write_readme(raw_rows, official_rows, excluded_rows)


if __name__ == "__main__":
    main()
