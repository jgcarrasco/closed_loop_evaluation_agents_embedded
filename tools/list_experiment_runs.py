from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_ROOT = REPO_ROOT / "experiments" / "results"


def _load_records(results_root: Path) -> list[dict[str, object]]:
    records = []
    for record_path in results_root.glob("*/*/*/evaluation.json"):
        records.append(json.loads(record_path.read_text(encoding="utf-8")))
    records.sort(key=lambda item: str(item.get("timestamp", "")), reverse=True)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="List recorded experiment runs.")
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--task-id", default="")
    parser.add_argument("--agent-name", default="")
    parser.add_argument("--benchmark-mode", default="")
    parser.add_argument("--status", default="")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    results_root = args.results_root.resolve()
    if not results_root.exists():
        print(f"No results directory exists at {results_root}")
        return 0

    records = _load_records(results_root)
    filtered = []
    for record in records:
        if args.task_id and record.get("task_id") != args.task_id:
            continue
        if args.agent_name and record.get("agent_name") != args.agent_name:
            continue
        if args.benchmark_mode and record.get("benchmark", {}).get("mode") != args.benchmark_mode:
            continue
        if args.status and record.get("status") != args.status:
            continue
        filtered.append(record)

    for record in filtered[: args.limit]:
        benchmark = record.get("benchmark", {})
        benchmark_mode = benchmark.get("mode", "")
        hidden_status = record.get("hidden_status", {})
        hidden_status_text = hidden_status.get("status", "")
        print(
            f"{record['timestamp']}  {record['task_id']}  {record['agent_name']}  "
            f"{benchmark_mode}  {record['status']}  {hidden_status_text}  {record['hidden_run_dir']}"
        )

    if not filtered:
        print("No recorded runs matched the requested filters.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
