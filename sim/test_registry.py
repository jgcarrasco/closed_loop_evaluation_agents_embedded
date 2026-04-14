from __future__ import annotations

import unittest
from pathlib import Path

from sim.task_spec import load_task_spec
from sim.tasks.registry import available_task_ids, load_task_runtime


REPO_ROOT = Path(__file__).resolve().parents[1]


class RegistryTests(unittest.TestCase):
    def test_registry_lists_current_tasks(self) -> None:
        self.assertIn("tank_fill_drain", available_task_ids())
        self.assertIn("thermal_chamber_hysteresis", available_task_ids())
        self.assertIn("pressure_vessel_interlock", available_task_ids())
        self.assertIn("mixing_tank_fill_heat", available_task_ids())
        self.assertIn("filter_tank_sequence", available_task_ids())

    def test_registry_loads_runtime_for_task_spec(self) -> None:
        spec = load_task_spec(REPO_ROOT / "specs" / "thermal_chamber_hysteresis.json")
        runtime = load_task_runtime(spec)

        self.assertIn("overshoot_guard", runtime.scenario_specs(spec))

    def test_registry_loads_hardest_runtime(self) -> None:
        spec = load_task_spec(REPO_ROOT / "specs" / "filter_tank_sequence.json")
        runtime = load_task_runtime(spec)

        self.assertIn("disturbance_recovery", runtime.scenario_specs(spec))


if __name__ == "__main__":
    unittest.main(verbosity=2)
