#!/usr/bin/env python3
"""Generate evaluation figures for the manuscript.

This script reads the official `paper_closed_loop_eval_420` bundle and writes
paper figures under ``docs/latex/figures/``.

Usage:
    /tmp/ai_embedded_plot_venv/bin/python docs/latex/scripts/generate_eval_figures.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from math import sqrt
from pathlib import Path
from statistics import fmean

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch


REPO_ROOT = Path(__file__).resolve().parents[3]
FIG_DIR = REPO_ROOT / "docs" / "latex" / "figures"
BUNDLE_SUMMARY_PATH = (
    REPO_ROOT / "artifacts" / "evaluations" / "paper_closed_loop_eval_420" / "summary.json"
)

TASK_ORDER = [
    "tank_fill_drain",
    "thermal_chamber_hysteresis",
    "pressure_vessel_interlock",
    "mixing_tank_fill_heat",
    "filter_tank_sequence",
]

MODE_ORDER = [
    "oneshot_blind",
    "realistic_self_verify",
    "ci_red_green",
    "oracle_full",
]

MODE_LABELS = {
    "oneshot_blind": "One-shot blind",
    "realistic_self_verify": "Realistic self-verify",
    "ci_red_green": "CI red/green",
    "oracle_full": "Oracle full",
}

MODEL_LABELS = {
    "gpt-5.4": "gpt-5.4",
    "gpt-5.4-mini": "gpt-5.4-mini",
    "qwen35-27b-q4km": "qwen3.5-27B",
    "qwen35-35b-a3b-ud-q4km": "qwen3.5-35B-A3B",
    "qwen35-9b-ud-q4kxl": "qwen3.5-9B",
    "qwen35-4b-ud-q4kxl": "qwen3.5-4B",
    "qwen35-2b-ud-q4kxl": "qwen3.5-2B",
}

MODEL_COLORS = {
    "gpt-5.4": "#1f77b4",
    "gpt-5.4-mini": "#76b7eb",
    "qwen3.5-27B": "#f28e2b",
    "qwen3.5-35B-A3B": "#e15759",
    "qwen3.5-9B": "#59a14f",
    "qwen3.5-4B": "#9c755f",
    "qwen3.5-2B": "#bab0ab",
}

REALISTIC_MODELS = [
    "gpt-5.4",
    "gpt-5.4-mini",
    "qwen3.5-27B",
    "qwen3.5-35B-A3B",
    "qwen3.5-9B",
    "qwen3.5-4B",
    "qwen3.5-2B",
]

LOCAL_MODELS = [
    "qwen3.5-27B",
    "qwen3.5-35B-A3B",
    "qwen3.5-9B",
    "qwen3.5-4B",
    "qwen3.5-2B",
]

LOCAL_SHORT_LABELS = {
    "qwen3.5-27B": "27B",
    "qwen3.5-35B-A3B": "35B-A3B",
    "qwen3.5-9B": "9B",
    "qwen3.5-4B": "4B",
    "qwen3.5-2B": "2B",
}

FAILURE_ORDER = [
    "pass",
    "host_tests",
    "integration",
    "no_submission",
]

FAILURE_LABELS = {
    "pass": "Pass",
    "host_tests": "Host-test failure",
    "integration": "Integration failure",
    "no_submission": "No submission",
}

FAILURE_SHORT_LABELS = {
    "pass": "PASS",
    "host_tests": "HOST",
    "integration": "INT",
    "no_submission": "NONE",
}

FAILURE_COLORS = {
    "pass": "#d8f0d2",
    "host_tests": "#e15759",
    "integration": "#f28e2b",
    "no_submission": "#9d9da1",
}

EXPECTED_REPETITIONS_PER_CELL = 3


def canonical_model(raw_label: str) -> str:
    if raw_label not in MODEL_LABELS:
        raise KeyError(f"Unexpected model label: {raw_label}")
    return MODEL_LABELS[raw_label]


def load_runs() -> list[dict]:
    rows: list[dict] = []
    for data in json.loads(BUNDLE_SUMMARY_PATH.read_text()):
        raw_label = data["model"]["label"]
        rows.append(
            {
                "model": canonical_model(raw_label),
                "raw_model": raw_label,
                "task": data["task_id"],
                "mode": data["mode"],
                "status": data["final_hidden_outcome"]["status"],
                "pass": bool(data["final_hidden_outcome"]["pass_fail"]),
                "infra_failure": bool(data["final_hidden_outcome"].get("infra_failure")),
                "failure_family": data["final_hidden_outcome"]["failure_family"],
                "stage": data["final_hidden_outcome"]["stage_reached"],
                "wall_clock_seconds": data["efficiency"]["wall_clock_seconds"],
                "first_submit_seconds": data["efficiency"]["time_to_first_submission_seconds"],
                "hidden_eval_calls": data["efficiency"]["hidden_eval_calls"],
                "build_attempts": data["efficiency"]["build_attempts"],
                "total_tokens": data["model_usage"]["total_tokens"],
                "tool_call_count": data["tool_behavior"]["tool_call_count"],
                "self_test_runs": data["testing_behavior"]["self_test_runs"],
            }
        )
    return rows


def require_complete_grid(rows: list[dict], models: list[str], modes: list[str], tasks: list[str]) -> None:
    expected = {(model, mode, task) for model in models for mode in modes for task in tasks}
    seen = {(row["model"], row["mode"], row["task"]) for row in rows}
    missing = sorted(expected - seen)
    if missing:
        raise RuntimeError(f"Missing expected runs: {missing[:8]}{' ...' if len(missing) > 8 else ''}")


def wilson_interval_pct(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    phat = successes / total
    denom = 1.0 + (z * z) / total
    center = (phat + (z * z) / (2.0 * total)) / denom
    half = z * sqrt((phat * (1.0 - phat) / total) + ((z * z) / (4.0 * total * total))) / denom
    low = max(0.0, 100.0 * (center - half))
    high = min(100.0, 100.0 * (center + half))
    return (low, high)


def plot_realistic_heatmap(rows: list[dict]) -> None:
    filtered = [r for r in rows if r["mode"] == "realistic_self_verify" and r["model"] in REALISTIC_MODELS]
    require_complete_grid(filtered, REALISTIC_MODELS, ["realistic_self_verify"], TASK_ORDER)

    pass_matrix = np.zeros((len(TASK_ORDER), len(REALISTIC_MODELS)), dtype=float)
    pass_labels = [["" for _ in REALISTIC_MODELS] for _ in TASK_ORDER]
    failure_matrix = np.zeros((len(TASK_ORDER), len(REALISTIC_MODELS)), dtype=int)
    failure_labels = [["" for _ in REALISTIC_MODELS] for _ in TASK_ORDER]
    failure_to_idx = {family: idx for idx, family in enumerate(FAILURE_ORDER)}

    lookup: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in filtered:
        lookup[(row["task"], row["model"])].append(row)
    for i, task in enumerate(TASK_ORDER):
        for j, model in enumerate(REALISTIC_MODELS):
            cell_rows = lookup[(task, model)]
            pass_count = sum(r["pass"] for r in cell_rows)
            total = len(cell_rows)
            pass_matrix[i, j] = pass_count / total
            pass_labels[i][j] = f"{pass_count}/{total}"

            outcomes = []
            for row in cell_rows:
                if row["pass"]:
                    outcomes.append("pass")
                elif row["failure_family"] in failure_to_idx:
                    outcomes.append(row["failure_family"])
                else:
                    outcomes.append("integration")
            most_likely_outcome = Counter(outcomes).most_common(1)[0][0]
            failure_matrix[i, j] = failure_to_idx[most_likely_outcome]
            failure_labels[i][j] = FAILURE_SHORT_LABELS[most_likely_outcome]

    fig, (ax_pass, ax_failure) = plt.subplots(
        1,
        2,
        figsize=(12.8, 5.8),
        gridspec_kw={"width_ratios": [1.0, 1.0]},
        sharey=True,
    )

    pass_image = ax_pass.imshow(pass_matrix, cmap="RdYlGn", vmin=0.0, vmax=1.0, aspect="auto")
    failure_image = ax_failure.imshow(
        failure_matrix,
        cmap=ListedColormap([FAILURE_COLORS[key] for key in FAILURE_ORDER]),
        vmin=-0.5,
        vmax=len(FAILURE_ORDER) - 0.5,
        aspect="auto",
    )

    for ax in (ax_pass, ax_failure):
        ax.set_xticks(range(len(REALISTIC_MODELS)))
        ax.set_xticklabels(REALISTIC_MODELS, rotation=18, ha="right")
        ax.set_yticks(range(len(TASK_ORDER)))
        ax.set_yticklabels(TASK_ORDER)
        ax.set_xticks(np.arange(-0.5, len(REALISTIC_MODELS), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(TASK_ORDER), 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.2)
        ax.tick_params(which="minor", bottom=False, left=False)

    ax_pass.set_ylabel("Task")
    ax_pass.set_title("Pass Count")
    ax_failure.set_title("Most Likely Outcome")

    for i in range(len(TASK_ORDER)):
        for j in range(len(REALISTIC_MODELS)):
            ax_pass.text(j, i, pass_labels[i][j], ha="center", va="center", fontsize=9.5, fontweight="bold")
            ax_failure.text(
                j,
                i,
                failure_labels[i][j],
                ha="center",
                va="center",
                fontsize=8.8,
                fontweight="bold",
            )

    colorbar = fig.colorbar(
        pass_image,
        ax=ax_pass,
        fraction=0.046,
        pad=0.04,
    )
    colorbar.set_ticks([0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0])
    colorbar.set_ticklabels(["0%", "33%", "67%", "100%"])
    colorbar.set_label("Pass rate across three repetitions")

    failure_handles = [
        Patch(facecolor=FAILURE_COLORS[key], edgecolor="black", label=FAILURE_LABELS[key])
        for key in FAILURE_ORDER
    ]
    ax_failure.legend(
        handles=failure_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.26),
        ncol=4,
        frameon=False,
        fontsize=8.6,
    )

    fig.supxlabel("Model", y=0.08)
    fig.subplots_adjust(bottom=0.30, left=0.07, right=0.98, top=0.88, wspace=0.16)
    fig.savefig(FIG_DIR / "realistic_self_verify_heatmap.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_scenario_sensitivity(rows: list[dict]) -> None:
    models = REALISTIC_MODELS
    filtered = [r for r in rows if r["model"] in models]
    require_complete_grid(filtered, models, MODE_ORDER, TASK_ORDER)

    pass_rates: dict[str, list[float]] = defaultdict(list)
    lower_errors: dict[str, list[float]] = defaultdict(list)
    upper_errors: dict[str, list[float]] = defaultdict(list)
    for model in models:
        model_rows = [r for r in filtered if r["model"] == model]
        for mode in MODE_ORDER:
            mode_rows = [r for r in model_rows if r["mode"] == mode]
            successes = sum(r["pass"] for r in mode_rows)
            total = len(mode_rows)
            rate = 100.0 * successes / total
            low, high = wilson_interval_pct(successes, total)
            pass_rates[model].append(rate)
            lower_errors[model].append(rate - low)
            upper_errors[model].append(high - rate)

    x = np.arange(len(MODE_ORDER))
    width = 0.10
    offsets = np.linspace(-(len(models) - 1) * width / 2.0, (len(models) - 1) * width / 2.0, len(models))

    fig, ax = plt.subplots(figsize=(11.6, 4.4))
    for offset, model in zip(offsets, models):
        heights = pass_rates[model]
        ax.bar(
            x + offset,
            heights,
            width=width,
            color=MODEL_COLORS[model],
            label=model,
            edgecolor="black",
            linewidth=0.4,
            yerr=np.vstack([lower_errors[model], upper_errors[model]]),
            capsize=2.3,
            error_kw={"elinewidth": 0.9, "capthick": 0.9, "ecolor": "#2f2f2f"},
        )

    ax.set_xticks(x)
    ax.set_xticklabels([MODE_LABELS[m] for m in MODE_ORDER])
    ax.set_ylabel("Pass rate across available runs (%)")
    ax.set_ylim(-3.0, 108)
    ax.grid(axis="y", linestyle=":", linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.28), ncol=4, frameon=False)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "scenario_sensitivity_pass_rates.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_local_tradeoff(rows: list[dict]) -> None:
    filtered = [r for r in rows if r["model"] in LOCAL_MODELS]
    require_complete_grid(filtered, LOCAL_MODELS, MODE_ORDER, TASK_ORDER)

    metrics = {}
    for model in LOCAL_MODELS:
        model_rows = [r for r in filtered if r["model"] == model]
        first_submit_values = [r["first_submit_seconds"] for r in model_rows if r["first_submit_seconds"] is not None]
        metrics[model] = {
            "pass_rate_pct": 100.0 * sum(r["pass"] for r in model_rows) / len(model_rows),
            "avg_first_submit_min": fmean(first_submit_values) / 60.0,
            "avg_tokens_m": fmean(r["total_tokens"] for r in model_rows) / 1_000_000.0,
        }

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.9), sharey=True)
    ax_time, ax_tokens = axes

    time_offsets = {
        "qwen3.5-27B": (-14, 8),
        "qwen3.5-35B-A3B": (6, 10),
        "qwen3.5-9B": (6, -10),
        "qwen3.5-4B": (6, 6),
        "qwen3.5-2B": (6, 6),
    }
    token_offsets = {
        "qwen3.5-27B": (6, 8),
        "qwen3.5-35B-A3B": (6, 10),
        "qwen3.5-9B": (6, -10),
        "qwen3.5-4B": (6, 6),
        "qwen3.5-2B": (-18, 8),
    }

    for model in LOCAL_MODELS:
        marker = "D" if model == "qwen3.5-35B-A3B" else "o"
        point = metrics[model]
        style = {
            "s": 92,
            "c": MODEL_COLORS[model],
            "marker": marker,
            "edgecolors": "black",
            "linewidths": 0.8,
            "alpha": 0.95,
        }
        ax_time.scatter(point["avg_first_submit_min"], point["pass_rate_pct"], **style)
        ax_tokens.scatter(point["avg_tokens_m"], point["pass_rate_pct"], **style)

        ax_time.annotate(
            LOCAL_SHORT_LABELS[model],
            (point["avg_first_submit_min"], point["pass_rate_pct"]),
            xytext=time_offsets[model],
            textcoords="offset points",
            fontsize=9,
            ha="left" if time_offsets[model][0] >= 0 else "right",
            va="center",
        )
        ax_tokens.annotate(
            LOCAL_SHORT_LABELS[model],
            (point["avg_tokens_m"], point["pass_rate_pct"]),
            xytext=token_offsets[model],
            textcoords="offset points",
            fontsize=9,
            ha="left" if token_offsets[model][0] >= 0 else "right",
            va="center",
        )

    ax_time.set_title("Submission Latency")
    ax_time.set_xlabel("Average first submission time (minutes)")
    ax_time.set_ylabel("Pass rate across available runs (%)")
    ax_time.set_xlim(-0.2, 19.5)
    ax_time.set_ylim(-3.0, 70.0)
    ax_time.grid(True, linestyle=":", linewidth=0.7, alpha=0.7)
    ax_time.set_axisbelow(True)

    ax_tokens.set_title("Token Demand")
    ax_tokens.set_xlabel("Average total tokens per run (millions)")
    ax_tokens.set_xscale("log")
    ax_tokens.set_xlim(2.2, 90.0)
    ax_tokens.set_xticks([3, 10, 30, 60])
    ax_tokens.set_xticklabels(["3", "10", "30", "60"])
    ax_tokens.grid(True, linestyle=":", linewidth=0.7, alpha=0.7)
    ax_tokens.set_axisbelow(True)

    marker_handles = [
        Line2D([0], [0], marker="o", linestyle="", color="black", markerfacecolor="white", label="Dense"),
        Line2D([0], [0], marker="D", linestyle="", color="black", markerfacecolor="white", label="MoE"),
    ]
    ax_tokens.legend(
        handles=marker_handles,
        title="Model form",
        loc="upper right",
        frameon=False,
    )

    fig.subplots_adjust(bottom=0.14, left=0.08, right=0.98, top=0.90, wspace=0.18)
    fig.savefig(FIG_DIR / "local_qwen_tradeoff.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_runs()
    plot_realistic_heatmap(rows)
    plot_scenario_sensitivity(rows)
    plot_local_tradeoff(rows)
    print(f"Wrote figures to {FIG_DIR}")


if __name__ == "__main__":
    main()
