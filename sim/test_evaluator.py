from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sim.evaluator import aggregate_results, write_trace_csv
from sim.tasks.base import ScenarioResult, TraceSample


class EvaluatorTests(unittest.TestCase):
    def test_aggregate_results_tracks_first_failure(self) -> None:
        aggregate = aggregate_results(
            [
                ScenarioResult(name="smoke", passed=True, reason="ok", metrics={"constraint_violations": 0}),
                ScenarioResult(
                    name="overshoot_guard",
                    passed=False,
                    reason="temperature exceeded the hard upper limit",
                    metrics={
                        "constraint_violations": 1,
                        "overshoot": 3,
                        "hard_limit_margin_c": -1,
                    },
                ),
            ]
        )

        self.assertFalse(aggregate["passed"])
        self.assertEqual("overshoot_guard", aggregate["failure_category"])
        self.assertEqual(1, aggregate["metrics"]["failed_scenarios"])
        self.assertEqual(1, aggregate["metrics"]["total_constraint_violations"])
        self.assertEqual(3.0, aggregate["metrics"]["max_overshoot"])
        self.assertEqual(-1.0, aggregate["metrics"]["minimum_hard_limit_margin_c"])

    def test_write_trace_csv_handles_dynamic_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = Path(tmpdir) / "trace.csv"
            write_trace_csv(
                trace_path,
                [
                    TraceSample(timestamp_ms=0, values={"temperature_c": 28, "heater_on": False}),
                    TraceSample(timestamp_ms=100, values={"temperature_c": 31, "heater_on": True, "retained_heat_c": 2}),
                ],
            )

            trace_text = trace_path.read_text(encoding="ascii")

        self.assertIn("timestamp_ms,temperature_c,heater_on,retained_heat_c", trace_text)
        self.assertIn("100,31,True,2", trace_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
