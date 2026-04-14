from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sim.tasks.base import ScenarioResult, TraceSample


def write_trace_csv(path: Path, samples: list[TraceSample]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    field_names: list[str] = []
    for sample in samples:
        for name in sample.values.keys():
            if name not in field_names:
                field_names.append(name)

    with path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["timestamp_ms", *field_names])
        for sample in samples:
            writer.writerow([sample.timestamp_ms, *[sample.values.get(name, "") for name in field_names]])


def aggregate_results(results: list[ScenarioResult]) -> dict[str, Any]:
    if not results:
        return {
            "passed": False,
            "failure_category": "no_scenarios",
            "scenario_count": 0,
            "metrics": {},
            "scenarios": [],
        }

    first_failure = next((result for result in results if not result.passed), None)
    aggregate_metrics = {
        "passed_scenarios": sum(1 for result in results if result.passed),
        "failed_scenarios": sum(1 for result in results if not result.passed),
    }
    if all("constraint_violations" in result.metrics for result in results):
        aggregate_metrics["total_constraint_violations"] = sum(
            int(result.metrics.get("constraint_violations", 0) or 0) for result in results
        )
    if any("overshoot" in result.metrics for result in results):
        aggregate_metrics["max_overshoot"] = max(float(result.metrics.get("overshoot", 0) or 0) for result in results)
    if any("hard_limit_margin_c" in result.metrics for result in results):
        aggregate_metrics["minimum_hard_limit_margin_c"] = min(
            float(result.metrics.get("hard_limit_margin_c", 0) or 0) for result in results
        )

    return {
        "passed": all(result.passed for result in results),
        "failure_category": "none" if first_failure is None else first_failure.name,
        "scenario_count": len(results),
        "metrics": aggregate_metrics,
        "scenario_metrics": {result.name: result.metrics for result in results},
        "scenarios": [result.to_json() for result in results],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
