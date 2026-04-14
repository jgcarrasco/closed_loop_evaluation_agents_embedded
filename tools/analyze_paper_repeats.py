#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = REPO_ROOT / "artifacts" / "evaluations"
DOCS_ROOT = REPO_ROOT / "docs"

MIXED_BASELINE_ROOT = EVAL_ROOT / "pi_matrix_20260324T125039Z"
MIXED_BASELINE_RUNS = 60

MODEL_DISPLAY = {
    "gpt-5.4": "gpt-5.4",
    "gpt-5.4-mini": "gpt-5.4-mini",
    "qwen35-27b-q4km": "qwen3.5-27B",
    "qwen35-35b-a3b-ud-q4km": "qwen3.5-35B-A3B",
    "qwen35-9b-ud-q4kxl": "qwen3.5-9B",
    "qwen35-4b-ud-q4kxl": "qwen3.5-4B",
    "qwen35-2b-ud-q4kxl": "qwen3.5-2B",
}

MIXED_MODELS = ("gpt-5.4", "gpt-5.4-mini", "qwen35-27b-q4km")
LOCAL_MODELS = (
    "qwen35-35b-a3b-ud-q4km",
    "qwen35-27b-q4km",
    "qwen35-9b-ud-q4kxl",
    "qwen35-4b-ud-q4kxl",
    "qwen35-2b-ud-q4kxl",
)

PAPER_REALISTIC_BASELINE = {
    "gpt-5.4": {"runs": 5, "passes": 5, "avg_total_tokens": 0.38, "avg_tool_calls": 33.4, "avg_hidden_evals": 1.0, "avg_self_test_runs": 3.0},
    "gpt-5.4-mini": {"runs": 5, "passes": 3, "avg_total_tokens": 1.01, "avg_tool_calls": 55.2, "avg_hidden_evals": 1.4, "avg_self_test_runs": 5.4},
    "qwen35-27b-q4km": {"runs": 5, "passes": 4, "avg_total_tokens": 3.50, "avg_tool_calls": 83.6, "avg_hidden_evals": 1.6, "avg_self_test_runs": 14.0},
    "qwen35-35b-a3b-ud-q4km": {"runs": 5, "passes": 1, "avg_total_tokens": 4.46, "avg_tool_calls": 94.8, "avg_hidden_evals": 1.2, "avg_self_test_runs": 26.2},
    "qwen35-9b-ud-q4kxl": {"runs": 5, "passes": 1, "avg_total_tokens": 6.98, "avg_tool_calls": 114.8, "avg_hidden_evals": 16.8, "avg_self_test_runs": 16.8},
    "qwen35-4b-ud-q4kxl": {"runs": 5, "passes": 1, "avg_total_tokens": 3.97, "avg_tool_calls": 87.0, "avg_hidden_evals": 1.8, "avg_self_test_runs": 25.0},
}

PAPER_LOCAL_BASELINE = {
    "qwen35-27b-q4km": {"runs": 20, "passes": 14, "form": "Dense", "avg_wall_clock": 26.6, "avg_first_submit": 16.5, "avg_total_tokens": 2.70, "avg_tool_calls": 63.9},
    "qwen35-35b-a3b-ud-q4km": {"runs": 20, "passes": 9, "form": "MoE", "avg_wall_clock": 16.9, "avg_first_submit": 12.8, "avg_total_tokens": 3.14, "avg_tool_calls": 68.5},
    "qwen35-9b-ud-q4kxl": {"runs": 20, "passes": 8, "form": "Dense", "avg_wall_clock": 20.4, "avg_first_submit": 13.7, "avg_total_tokens": 4.63, "avg_tool_calls": 86.9},
    "qwen35-4b-ud-q4kxl": {"runs": 20, "passes": 4, "form": "Dense", "avg_wall_clock": 16.7, "avg_first_submit": 6.8, "avg_total_tokens": 10.71, "avg_tool_calls": 163.4},
    "qwen35-2b-ud-q4kxl": {"runs": 20, "passes": 0, "form": "Dense", "avg_wall_clock": 35.2, "avg_first_submit": 0.7, "avg_total_tokens": 62.15, "avg_tool_calls": 800.2},
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _to_float(value: str | None) -> float | None:
    if value in (None, "", "None"):
        return None
    return float(value)


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


def _git_dirty() -> bool:
    completed = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, check=False, capture_output=True, text=True)
    return bool(completed.stdout.strip())


def _mixed_root(tag: str, replica: int) -> Path:
    return EVAL_ROOT / f"pi_matrix_paper_mixed_{tag}_rep{replica}"


def _local_root(tag: str, replica: int) -> Path:
    return EVAL_ROOT / f"pi_matrix_paper_local_{tag}_rep{replica}"


def _two_b_root(tag: str, replica: int) -> Path:
    return EVAL_ROOT / f"pi_matrix_paper_2b_{tag}_rep{replica}"


def _load_replication_rows(tag: str, replica: int) -> dict[str, list[dict[str, str]]]:
    mixed_rows = _read_csv(_mixed_root(tag, replica) / "summary.csv")
    local = _read_csv(_local_root(tag, replica) / "summary.csv")
    two_b = _read_csv(_two_b_root(tag, replica) / "summary.csv")
    return {"mixed": mixed_rows, "local": local + two_b}


def _status_triplet(row: dict[str, str]) -> str:
    return f"{row['hidden_status']} ({row['failure_family']})"


def _pass_count(rows: list[dict[str, str]]) -> int:
    return sum(row["pass_fail"] == "True" for row in rows)


def _avg(rows: list[dict[str, str]], field: str) -> float:
    values = [float(row[field]) for row in rows if row[field] not in ("", "None")]
    return sum(values) / len(values)


def _realistic_rows(rows: list[dict[str, str]], model_label: str) -> list[dict[str, str]]:
    return [row for row in rows if row["mode"] == "realistic_self_verify" and row["model_label"] == model_label]


def _combined_realistic(tag: str, mixed_replications: list[list[dict[str, str]]], local_replications: list[list[dict[str, str]]]) -> list[dict[str, str]]:
    lines: list[dict[str, str]] = []
    for model in ("gpt-5.4", "gpt-5.4-mini", "qwen35-27b-q4km", "qwen35-35b-a3b-ud-q4km", "qwen35-9b-ud-q4kxl", "qwen35-4b-ud-q4kxl"):
        baseline = PAPER_REALISTIC_BASELINE[model]
        rep_source = mixed_replications if model in MIXED_MODELS else local_replications
        rep_rows = []
        for rows in rep_source:
            rep_rows.extend(_realistic_rows(rows, model))
        rep_runs = len(rep_rows)
        total_runs = baseline["runs"] + rep_runs
        total_passes = baseline["passes"] + _pass_count(rep_rows)
        total_tokens = baseline["avg_total_tokens"] * baseline["runs"] + sum(float(row["total_tokens"]) for row in rep_rows) / 1_000_000
        total_tools = baseline["avg_tool_calls"] * baseline["runs"] + sum(float(row["tool_call_count"]) for row in rep_rows)
        total_evals = baseline["avg_hidden_evals"] * baseline["runs"] + sum(float(row["hidden_eval_calls"]) for row in rep_rows)
        total_tests = baseline["avg_self_test_runs"] * baseline["runs"] + sum(float(row["self_test_runs"]) for row in rep_rows)
        lines.append(
            {
                "model": MODEL_DISPLAY[model],
                "passes": f"{total_passes}/{total_runs}",
                "avg_total_tokens": f"{total_tokens / total_runs:.2f}M",
                "avg_tool_calls": f"{total_tools / total_runs:.1f}",
                "avg_hidden_evals": f"{total_evals / total_runs:.1f}",
                "avg_self_test_runs": f"{total_tests / total_runs:.1f}",
            }
        )
    return lines


def _combined_local(local_replications: list[list[dict[str, str]]]) -> list[dict[str, str]]:
    lines: list[dict[str, str]] = []
    for model in LOCAL_MODELS:
        baseline = PAPER_LOCAL_BASELINE[model]
        rep_rows = []
        for rows in local_replications:
            rep_rows.extend([row for row in rows if row["model_label"] == model])
        rep_runs = len(rep_rows)
        total_runs = baseline["runs"] + rep_runs
        total_passes = baseline["passes"] + _pass_count(rep_rows)
        total_wall = baseline["avg_wall_clock"] * baseline["runs"] + sum(float(row["wall_clock_seconds"]) for row in rep_rows) / 60.0
        total_first_submit = baseline["avg_first_submit"] * baseline["runs"] + sum(_to_float(row["time_to_first_submission_seconds"]) or 0.0 for row in rep_rows) / 60.0
        total_tokens = baseline["avg_total_tokens"] * baseline["runs"] + sum(float(row["total_tokens"]) for row in rep_rows) / 1_000_000
        total_tools = baseline["avg_tool_calls"] * baseline["runs"] + sum(float(row["tool_call_count"]) for row in rep_rows)
        lines.append(
            {
                "model": MODEL_DISPLAY[model],
                "form": baseline["form"],
                "passes": f"{total_passes}/{total_runs}",
                "avg_wall_clock": f"{total_wall / total_runs:.1f} min",
                "avg_first_submit": f"{total_first_submit / total_runs:.1f} min",
                "avg_total_tokens": f"{total_tokens / total_runs:.2f}M",
                "avg_tool_calls": f"{total_tools / total_runs:.1f}",
            }
        )
    return lines


def _mixed_flips(mixed_original: list[dict[str, str]], mixed_replications: list[list[dict[str, str]]]) -> list[str]:
    by_combo: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for row in mixed_original:
        by_combo[(row["task_id"], row["mode"], row["model_label"])].append(_status_triplet(row))
    for rows in mixed_replications:
        for row in rows:
            by_combo[(row["task_id"], row["mode"], row["model_label"])].append(_status_triplet(row))
    lines = []
    for (task_id, mode, model_label), statuses in sorted(by_combo.items()):
        unique = list(dict.fromkeys(statuses))
        if len(unique) > 1:
            pretty = ", ".join(unique)
            lines.append(f"- `{MODEL_DISPLAY[model_label]}` on `{task_id}` / `{mode}` changed across repetitions: {pretty}")
    return lines


def _local_replica_flips(local_replications: list[list[dict[str, str]]]) -> list[str]:
    by_combo: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for rows in local_replications:
        for row in rows:
            by_combo[(row["task_id"], row["mode"], row["model_label"])].append(_status_triplet(row))
    lines = []
    for (task_id, mode, model_label), statuses in sorted(by_combo.items()):
        unique = list(dict.fromkeys(statuses))
        if len(unique) > 1:
            pretty = ", ".join(unique)
            lines.append(f"- `{MODEL_DISPLAY[model_label]}` on `{task_id}` / `{mode}` differed between the two new local repetitions: {pretty}")
    return lines


def _mixed_summary(rows: list[dict[str, str]]) -> dict[str, int]:
    return {
        "runs": len(rows),
        "passes": _pass_count(rows),
        "infra_failures": sum(row["infra_failure"] == "True" for row in rows),
    }


def _local_summary(rows: list[dict[str, str]]) -> dict[str, int]:
    return {
        "runs": len(rows),
        "passes": _pass_count(rows),
        "infra_failures": sum(row["infra_failure"] == "True" for row in rows),
    }


def _realistic_passes(rep_rows: list[dict[str, str]], model_label: str) -> str:
    filtered = _realistic_rows(rep_rows, model_label)
    return f"{_pass_count(filtered)}/{len(filtered)}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze two additional paper repeat sweeps and write a markdown report.")
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()

    mixed_original = _read_csv(MIXED_BASELINE_ROOT / "summary.csv")
    replications = [_load_replication_rows(args.tag, 1), _load_replication_rows(args.tag, 2)]
    mixed_replications = [rep["mixed"] for rep in replications]
    local_replications = [rep["local"] for rep in replications]

    mixed_reports = [_mixed_summary(rows) for rows in mixed_replications]
    local_reports = [_local_summary(rows) for rows in local_replications]

    realistic_table = _combined_realistic(args.tag, mixed_replications, local_replications)
    local_table = _combined_local(local_replications)

    mixed_flips = _mixed_flips(mixed_original, mixed_replications)
    local_flips = _local_replica_flips(local_replications)

    gpt54_realistic_passes = PAPER_REALISTIC_BASELINE["gpt-5.4"]["passes"] + sum(
        _pass_count(_realistic_rows(rows, "gpt-5.4")) for rows in mixed_replications
    )
    gpt54_realistic_runs = PAPER_REALISTIC_BASELINE["gpt-5.4"]["runs"] + sum(
        len(_realistic_rows(rows, "gpt-5.4")) for rows in mixed_replications
    )
    gpt54_all_passes = _pass_count(mixed_original) + sum(_pass_count(rows) for rows in mixed_replications if rows)
    gpt54_all_runs = len([row for row in mixed_original if row["model_label"] == "gpt-5.4"]) + sum(
        len([row for row in rows if row["model_label"] == "gpt-5.4"]) for rows in mixed_replications
    )

    local_best_row = max(local_table, key=lambda row: int(row["passes"].split("/")[0]))

    report_path = DOCS_ROOT / f"paper_repeat_report_{args.tag}.md"
    lines = [
        f"# Paper Repeat Report ({args.tag})",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
        f"- HEAD: `{_git_head()}`",
        f"- Worktree dirty at launch/analyze time: `{'yes' if _git_dirty() else 'no'}`",
        f"- Mixed baseline root: `{MIXED_BASELINE_ROOT}`",
        f"- Replication 1 roots: `{_mixed_root(args.tag, 1)}`, `{_local_root(args.tag, 1)}`, `{_two_b_root(args.tag, 1)}`",
        f"- Replication 2 roots: `{_mixed_root(args.tag, 2)}`, `{_local_root(args.tag, 2)}`, `{_two_b_root(args.tag, 2)}`",
        "",
        "## New Replication Summary",
        "",
        f"- Replication 1 mixed-model matrix: `{mixed_reports[0]['passes']}/{mixed_reports[0]['runs']}` passes, `{mixed_reports[0]['infra_failures']}` infrastructure failures",
        f"- Replication 2 mixed-model matrix: `{mixed_reports[1]['passes']}/{mixed_reports[1]['runs']}` passes, `{mixed_reports[1]['infra_failures']}` infrastructure failures",
        f"- Replication 1 local study: `{local_reports[0]['passes']}/{local_reports[0]['runs']}` passes, `{local_reports[0]['infra_failures']}` infrastructure failures",
        f"- Replication 2 local study: `{local_reports[1]['passes']}/{local_reports[1]['runs']}` passes, `{local_reports[1]['infra_failures']}` infrastructure failures",
        "",
        "## Result Changes",
        "",
        "### Mixed-Model Cells That Flipped Versus The Original Paper Sweep",
        "",
    ]

    if mixed_flips:
        lines.extend(mixed_flips)
    else:
        lines.append("- No mixed-model cell changed status relative to the original 60-run sweep.")

    lines.extend(
        [
            "",
            "### Local Cells That Flipped Between The Two New Repetitions",
            "",
        ]
    )
    if local_flips:
        lines.extend(local_flips)
    else:
        lines.append("- No local cell changed status between the two new repetitions.")

    lines.extend(
        [
            "",
            "## Updated Realistic Self-Verify Table",
            "",
            "This is the table I would use if the manuscript is updated to report three total repetitions per relevant cell in the primary scenario.",
            "",
            "| Model | Passes | Avg total tokens | Avg tool calls | Avg hidden evals | Avg self-test runs |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in realistic_table:
        lines.append(
            f"| {row['model']} | {row['passes']} | {row['avg_total_tokens']} | {row['avg_tool_calls']} | {row['avg_hidden_evals']} | {row['avg_self_test_runs']} |"
        )

    lines.extend(
        [
            "",
            "## Updated Local-Only Table",
            "",
            "This is the table I would use if the manuscript is updated to report 60 total runs per local model in the shared-hardware study.",
            "",
            "| Model | Form | Passes | Avg wall-clock | Avg first submit | Avg total tokens | Avg tool calls |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in local_table:
        lines.append(
            f"| {row['model']} | {row['form']} | {row['passes']} | {row['avg_wall_clock']} | {row['avg_first_submit']} | {row['avg_total_tokens']} | {row['avg_tool_calls']} |"
        )

    lines.extend(
        [
            "",
            "## Paper Changes I Would Make",
            "",
        ]
    )

    if gpt54_realistic_passes == gpt54_realistic_runs:
        lines.append(f"- The claim that `gpt-5.4` saturates `realistic_self_verify` still holds over `{gpt54_realistic_passes}/{gpt54_realistic_runs}` primary-scenario runs, but the wording should be variance-aware instead of relying on a single run per cell.")
    else:
        lines.append(f"- Remove the claim that `gpt-5.4` saturates `realistic_self_verify`; across three repetitions it is `{gpt54_realistic_passes}/{gpt54_realistic_runs}` instead of perfect.")

    gpt54_mixed_total_runs = len([row for row in mixed_original if row["model_label"] == "gpt-5.4"]) + sum(
        len([row for row in rows if row["model_label"] == "gpt-5.4"]) for rows in mixed_replications
    )
    gpt54_mixed_total_passes = sum(
        row["pass_fail"] == "True" for row in mixed_original if row["model_label"] == "gpt-5.4"
    ) + sum(_pass_count([row for row in rows if row["model_label"] == "gpt-5.4"]) for rows in mixed_replications)
    if gpt54_mixed_total_passes == gpt54_mixed_total_runs:
        lines.append(f"- The claim that `gpt-5.4` is invariant across the four scenarios still holds in the mixed-model matrix over `{gpt54_mixed_total_passes}/{gpt54_mixed_total_runs}` runs.")
    else:
        lines.append(f"- Remove or soften the claim that `gpt-5.4` is invariant across the four scenarios; it is `{gpt54_mixed_total_passes}/{gpt54_mixed_total_runs}` over the repeated mixed-model matrix.")

    lines.append("- Replace single-run-per-cell wording in the limitations section with a description of the repeated-run protocol and the observed cell volatility listed above.")
    lines.append("- Update Section 4 so that the primary table reports repeated-run totals or pass rates with confidence intervals instead of one-pass snapshots.")
    lines.append(f"- Update the local-only subsection to reflect that the current best local operating point remains `{local_best_row['model']}` only if that model still leads after 60 total runs.")
    lines.append("- Add a short paragraph explicitly distinguishing the cross-family `qwen3.5-27B` condition from the shared-hardware local `qwen3.5-27B` condition, because repeated reporting makes that ambiguity more visible.")
    lines.append("- If any mixed-model or local cell flipped, add a sentence in the discussion explaining that deterministic simulation does not remove agent/model variance; it only removes plant randomness.")
    lines.append("- Consider adding a supplementary CSV with all repeated-run cell outcomes, because the benchmark is now rich enough that readers will reasonably ask for per-repetition transparency.")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"report_path": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
