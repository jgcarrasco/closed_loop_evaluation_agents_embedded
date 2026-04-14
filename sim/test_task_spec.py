from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from sim.task_spec import load_task_spec


class TaskSpecTests(unittest.TestCase):
    REPO_ROOT = Path(__file__).resolve().parents[1]

    def test_loads_tank_spec(self) -> None:
        spec = load_task_spec(self.REPO_ROOT / "specs" / "tank_fill_drain.json")

        self.assertEqual(spec.task_id, "tank_fill_drain")
        self.assertEqual(spec.target_band, (30, 80))
        self.assertIn("happy_path", spec.scenario_names)

    def test_loads_thermal_spec(self) -> None:
        spec = load_task_spec(self.REPO_ROOT / "specs" / "thermal_chamber_hysteresis.json")

        self.assertEqual(spec.task_id, "thermal_chamber_hysteresis")
        self.assertEqual(spec.target_band, (47, 52))
        self.assertIn("overshoot_guard", spec.scenario_names)

    def test_renders_agent_summary(self) -> None:
        spec = load_task_spec(self.REPO_ROOT / "specs" / "tank_fill_drain.json")

        rendered = spec.render_agent_summary()
        self.assertIn("Control Policy", rendered)
        self.assertIn("Required scenarios", rendered)
        self.assertIn("Sensor: LEVEL", rendered)

    def test_renders_thermal_summary_sections(self) -> None:
        spec = load_task_spec(self.REPO_ROOT / "specs" / "thermal_chamber_hysteresis.json")

        rendered = spec.render_agent_summary()

        self.assertIn("Decision Summary", rendered)
        self.assertIn("State Model", rendered)
        self.assertIn("Sensor: TEMP", rendered)

    def test_loads_pressure_interlock_spec(self) -> None:
        spec = load_task_spec(self.REPO_ROOT / "specs" / "pressure_vessel_interlock.json")

        self.assertEqual(spec.task_id, "pressure_vessel_interlock")
        self.assertEqual(spec.target_band, (40, 60))
        self.assertIn("door_open_interlock", spec.scenario_names)

    def test_loads_mixing_tank_spec(self) -> None:
        spec = load_task_spec(self.REPO_ROOT / "specs" / "mixing_tank_fill_heat.json")

        self.assertEqual(spec.task_id, "mixing_tank_fill_heat")
        self.assertEqual(spec.target_band, (45, 48))
        self.assertIn("fill_then_heat", spec.scenario_names)

    def test_loads_filter_sequence_spec(self) -> None:
        spec = load_task_spec(self.REPO_ROOT / "specs" / "filter_tank_sequence.json")

        self.assertEqual(spec.task_id, "filter_tank_sequence")
        self.assertEqual(spec.target_band, (0, 35))
        self.assertIn("disturbance_recovery", spec.scenario_names)

    def test_renders_filter_sequence_summary_sections(self) -> None:
        spec = load_task_spec(self.REPO_ROOT / "specs" / "filter_tank_sequence.json")

        rendered = spec.render_agent_summary()

        self.assertIn("Decision Summary", rendered)
        self.assertIn("State Model", rendered)
        self.assertIn("Sensor: TURB", rendered)

    def test_public_contract_payload_hides_required_scenarios(self) -> None:
        spec = load_task_spec(self.REPO_ROOT / "specs" / "tank_fill_drain.json")

        payload = spec.public_contract_payload()

        self.assertNotIn("experiment_id", payload)
        self.assertNotIn("required_scenarios", payload["success"])
        self.assertIn("thresholds", payload["success"])
        self.assertEqual(payload["editable_paths"], spec.editable_paths)

    def test_workspace_generation_defaults_to_prose_only_and_writes_benchmark_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir) / "workspace"
            completed = subprocess.run(
                [
                    "python3",
                    str(self.REPO_ROOT / "tools" / "create_experiment_workspace.py"),
                    "tank_fill_drain",
                    str(workspace_root),
                    "--force",
                    "--skip-git-init",
                    "--benchmark-mode",
                    "ci_red_green",
                ],
                cwd=self.REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr or completed.stdout)

            experiment = json.loads((workspace_root / "experiment.json").read_text(encoding="utf-8"))

            self.assertEqual(experiment["benchmark"]["mode"], "ci_red_green")
            self.assertIn("agent_tests", experiment["local_paths"])
            self.assertEqual(experiment["public_task_contract"]["mode"], "prose_only")
            self.assertNotIn("docs/20_task_contract.json", experiment["task_docs"])
            self.assertFalse((workspace_root / "docs" / "20_task_contract.json").exists())

    def test_workspace_generation_can_include_public_contract_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir) / "workspace"
            completed = subprocess.run(
                [
                    "python3",
                    str(self.REPO_ROOT / "tools" / "create_experiment_workspace.py"),
                    "tank_fill_drain",
                    str(workspace_root),
                    "--force",
                    "--skip-git-init",
                    "--public-task-contract",
                    "json",
                ],
                cwd=self.REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr or completed.stdout)

            experiment = json.loads((workspace_root / "experiment.json").read_text(encoding="utf-8"))
            public_contract = json.loads((workspace_root / "docs" / "20_task_contract.json").read_text(encoding="utf-8"))

            self.assertEqual(experiment["public_task_contract"]["mode"], "json")
            self.assertIn("docs/20_task_contract.json", experiment["task_docs"])
            self.assertEqual(public_contract["task_id"], "tank_fill_drain")

    def test_oneshot_workspace_omits_visible_self_verification_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir) / "workspace"
            completed = subprocess.run(
                [
                    "python3",
                    str(self.REPO_ROOT / "tools" / "create_experiment_workspace.py"),
                    "tank_fill_drain",
                    str(workspace_root),
                    "--force",
                    "--skip-git-init",
                    "--benchmark-mode",
                    "oneshot_blind",
                ],
                cwd=self.REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr or completed.stdout)

            experiment = json.loads((workspace_root / "experiment.json").read_text(encoding="utf-8"))
            readme_text = (workspace_root / "README.md").read_text(encoding="utf-8")
            start_here_text = (workspace_root / "START_HERE.md").read_text(encoding="utf-8")
            common_text = (workspace_root / "docs" / "00_common_instructions.md").read_text(encoding="utf-8")

            self.assertEqual(experiment["benchmark"]["mode"], "oneshot_blind")
            self.assertNotIn("agent_tests", experiment["local_paths"])
            self.assertEqual(experiment["public_task_contract"]["mode"], "prose_only")
            self.assertFalse((workspace_root / "agent_tests").exists())
            self.assertFalse((workspace_root / "bench_public").exists())
            self.assertFalse((workspace_root / "tools" / "run_build.py").exists())
            self.assertFalse((workspace_root / "tools" / "run_self_tests.py").exists())
            self.assertFalse((workspace_root / "docs" / "20_task_contract.json").exists())
            self.assertIn("intentionally omitted", readme_text)
            self.assertIn("intentionally absent", start_here_text)
            self.assertIn("public self-verification helpers intentionally omitted", common_text)

    def test_prose_only_tasks_document_hidden_controller_state_assertions(self) -> None:
        task_root = self.REPO_ROOT / "experiments" / "tasks"
        state_pattern = re.compile(r"CONTROLLER_STATE_([A-Z0-9_]+)")

        for task_dir in sorted(path for path in task_root.iterdir() if path.is_dir()):
            task_md = task_dir / "task.md"
            host_test = self.REPO_ROOT / "host_tests" / "tasks" / task_dir.name / "test_controller.c"
            if not task_md.exists() or not host_test.exists():
                continue

            task_text = task_md.read_text(encoding="utf-8")
            host_text = host_test.read_text(encoding="utf-8")

            self.assertNotIn(
                "output.timed_out",
                host_text,
                msg=f"{task_dir.name} host tests grade undocumented timed_out semantics",
            )

            for state_name in sorted(set(state_pattern.findall(host_text))):
                self.assertIn(
                    f"`{state_name}`",
                    task_text,
                    msg=f"{task_dir.name} host tests grade undocumented controller state {state_name}",
                )

    def test_prose_only_tasks_document_hidden_runtime_hard_limits(self) -> None:
        task_root = self.REPO_ROOT / "experiments" / "tasks"

        for task_dir in sorted(path for path in task_root.iterdir() if path.is_dir()):
            task_md = task_dir / "task.md"
            spec_path = self.REPO_ROOT / "specs" / f"{task_dir.name}.json"
            if not task_md.exists() or not spec_path.exists():
                continue

            task_text = task_md.read_text(encoding="utf-8")
            spec_payload = json.loads(spec_path.read_text(encoding="utf-8"))
            thresholds = spec_payload.get("success", {}).get("thresholds", {})
            hard_upper_limit = thresholds.get("hard_upper_limit_c")
            if hard_upper_limit is None:
                continue

            self.assertIn(
                f"`{hard_upper_limit} C`",
                task_text,
                msg=f"{task_dir.name} hidden hard upper limit is not documented in the prose task brief",
            )

    def test_prose_only_tasks_ship_self_verification_checklists(self) -> None:
        task_root = self.REPO_ROOT / "experiments" / "tasks"

        for task_dir in sorted(path for path in task_root.iterdir() if path.is_dir()):
            task_md = task_dir / "task.md"
            if not task_md.exists():
                continue

            task_text = task_md.read_text(encoding="utf-8")
            self.assertIn(
                "## Self-Verification Checklist",
                task_text,
                msg=f"{task_dir.name} is missing a public self-verification checklist",
            )
            self.assertIn(
                "firmware-level end-to-end runtime probe",
                task_text,
                msg=f"{task_dir.name} is missing a public end-to-end runtime probe requirement",
            )

    def test_common_agent_instructions_require_checklist_coverage(self) -> None:
        common_text = (self.REPO_ROOT / "experiments" / "common" / "agent_workflow.md").read_text(encoding="utf-8")
        start_here_text = (self.REPO_ROOT / "experiments" / "base_workspace" / "START_HERE.md").read_text(encoding="utf-8")
        self_test_readme = (self.REPO_ROOT / "experiments" / "base_workspace" / "agent_tests" / "README.md").read_text(encoding="utf-8")

        self.assertIn("Self-Verification Checklist", common_text)
        self.assertIn("each explicit acceptance bullet", common_text)
        self.assertIn("each explicit acceptance bullet", start_here_text)
        self.assertIn("firmware-level end-to-end runtime probe", common_text)
        self.assertIn("firmware-level end-to-end runtime probe", start_here_text)
        self.assertIn("firmware-level end-to-end runtime probe", self_test_readme)


if __name__ == "__main__":
    unittest.main(verbosity=2)
