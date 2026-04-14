# Paper Closed-Loop Evaluation Bundle

This directory contains the official `420`-run artifact bundle used in the paper manuscript.

## Included Files

- `runs/`: `420` per-run directories under `artifacts/evaluations/paper_closed_loop_eval_420/runs/`.
- `summary.csv`, `summary.json`, `summary.md`, `aggregate_metrics.json`: top-level summaries for the full bundle.
- `official_run_index.csv`: one row per run with task, mode, model, outcome, and direct paths to the copied artifacts.
- `official_summary_by_model.csv` and `official_summary_by_model_mode.csv`: pooled pass summaries.

## Per-Run Artifacts

Each run directory contains:

- `prompt.txt`
- `session.jsonl`
- `pi_stdout.log`
- `pi_stderr.log`
- `summary.json`
