from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.evaluator import aggregate_results, write_json
from sim.scenarios import run_many, scenario_specs
from sim.task_spec import load_task_spec


DEFAULT_TASK_SPEC = Path(__file__).resolve().parents[1] / "specs" / "tank_fill_drain.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all QEMU-backed integration scenarios.")
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path("artifacts/stage8"),
        help="Directory for integration artifacts.",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        help="Only run selected scenarios. Repeat to run multiple scenarios.",
    )
    parser.add_argument(
        "--task-spec",
        type=Path,
        default=DEFAULT_TASK_SPEC,
        help="Structured task specification used for metrics and pass/fail thresholds.",
    )
    args = parser.parse_args()

    task_spec = load_task_spec(args.task_spec)
    available_names = set(scenario_specs(task_spec).keys())
    names = args.scenario or list(task_spec.scenario_names)
    unknown_names = [name for name in names if name not in available_names]
    if unknown_names:
        available_text = ", ".join(sorted(available_names))
        raise SystemExit(f"unknown scenario(s): {', '.join(unknown_names)}\navailable scenarios: {available_text}")
    try:
        results = run_many(names, args.artifact_dir, task_spec=task_spec, port=5555)
    except RuntimeError as exc:
        print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True))
        return 1
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    aggregate = aggregate_results(results)
    integration_log = args.artifact_dir / "integration.log"
    integration_log.write_text(
        "".join(f"{result.name}: {'PASS' if result.passed else 'FAIL'} - {result.reason}\n" for result in results),
        encoding="ascii",
    )
    write_json(args.artifact_dir / "summary.json", aggregate)
    write_json(args.artifact_dir / "metrics.json", aggregate.get("metrics", {}))

    payload = {
        "passed": aggregate["passed"],
        "failure_category": aggregate["failure_category"],
        "metrics": aggregate["metrics"],
        "scenarios": [result.to_json() for result in results],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if aggregate["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
