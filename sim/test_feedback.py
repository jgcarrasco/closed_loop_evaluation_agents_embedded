from __future__ import annotations

import unittest

from sim.feedback import normalize_feedback_config, project_feedback, render_feedback_markdown


class FeedbackTests(unittest.TestCase):
    def test_minimal_mode_hides_metrics(self) -> None:
        view = project_feedback(
            {
                "task": {"task_id": "tank_fill_drain"},
                "stages": {
                    "build": {"success": True, "returncode": 0, "duration_s": 1.0},
                    "flash_image": {"success": True, "returncode": 0, "duration_s": 1.0},
                    "qemu_smoke": {"success": True, "returncode": 0, "duration_s": 1.0},
                    "host_tests": {"success": True, "returncode": 0, "duration_s": 1.0},
                    "integration": {"success": True, "returncode": 0, "duration_s": 1.0},
                },
                "summary": {"status": "PASS", "task_solved": True, "failure_category": "none"},
                "metrics": {"aggregate": {"max_overshoot": 0}},
            },
            {"mode": "minimal"},
        )

        self.assertNotIn("metrics", view)
        self.assertEqual(view["summary"]["status"], "PASS")

    def test_full_mode_keeps_requested_sections(self) -> None:
        config = normalize_feedback_config({"mode": "full"})

        self.assertTrue(config["include_metrics"])
        self.assertTrue(config["include_build_logs"])

    def test_feedback_sanitizes_hidden_paths(self) -> None:
        view = project_feedback(
            {
                "task": {"task_id": "tank_fill_drain"},
                "stages": {
                    "host_tests": {
                        "success": False,
                        "returncode": 8,
                        "duration_s": 0.2,
                        "errors": [
                            "Assertion failed at /tmp/embedded_eval_hidden_harness/tank_fill_drain/run_1/host_tests/test_controller.c:35: output.pump_on"
                        ],
                        "stdout_tail": (
                            "Built /tmp/embedded_eval_hidden_harness/tank_fill_drain/run_1/"
                            "components/controller/controller.c.o"
                        ),
                    },
                },
                "summary": {"status": "HOST_TEST_FAILED", "task_solved": False, "failure_category": "host_tests"},
            },
            {"mode": "full"},
        )

        error_line = view["tests"]["host_unit_tests"]["errors"][0]
        stdout_tail = view["tests"]["host_unit_tests"]["stdout_tail"]
        markdown = render_feedback_markdown(view)

        self.assertIn("hidden_harness:host_tests/test_controller.c:35", error_line)
        self.assertNotIn("/tmp/embedded_eval_hidden_harness", error_line)
        self.assertIn("hidden_harness:components/controller/controller.c.o", stdout_tail)
        self.assertNotIn("/tmp/embedded_eval_hidden_harness", stdout_tail)
        self.assertIn("hidden_harness:host_tests/test_controller.c:35", markdown)
        self.assertNotIn("/tmp/embedded_eval_hidden_harness", markdown)

    def test_feedback_surfaces_failed_integration_scenarios(self) -> None:
        view = project_feedback(
            {
                "task": {"task_id": "tank_fill_drain"},
                "stages": {
                    "integration": {
                        "success": False,
                        "returncode": 1,
                        "duration_s": 9.5,
                        "errors": [
                            "\"name\": \"happy_path\"",
                            "\"reason\": \"plant never crossed the upper threshold\"",
                        ],
                    },
                },
                "metrics": {
                    "integration": {
                        "scenarios": [
                            {
                                "name": "happy_path",
                                "passed": False,
                                "reason": "plant never crossed the upper threshold",
                                "checks": {
                                    "threshold_crossed": False,
                                    "off_after_threshold": False,
                                },
                                "saw_pump_on": True,
                                "metrics": {
                                    "initial_level": 20,
                                    "min_level": 0,
                                    "max_level": 20,
                                    "final_level": 0,
                                    "oscillation_detected": True,
                                    "pump_transitions": 56,
                                    "sample_count": 85,
                                },
                            },
                            {
                                "name": "sensor_timeout",
                                "passed": False,
                                "reason": "timeout-driven PUMP OFF was not observed",
                                "checks": {
                                    "timeout_off_detected": False,
                                },
                                "last_valid_send_ms": 300,
                                "timeout_off_delta_ms": None,
                                "metrics": {
                                    "initial_level": 20,
                                    "min_level": 0,
                                    "max_level": 20,
                                    "final_level": 0,
                                    "oscillation_detected": True,
                                    "pump_transitions": 8,
                                    "sample_count": 31,
                                },
                            },
                            {
                                "name": "malformed_frame",
                                "passed": True,
                                "reason": "malformed input triggered safe-off behavior",
                                "checks": {"safe_off_after_invalid": True},
                            },
                        ],
                    },
                },
                "summary": {"status": "INTEGRATION_FAILED", "task_solved": False, "failure_category": "happy_path"},
            },
            {"mode": "full"},
        )

        failed_scenarios = view["tests"]["integration"]["failed_scenarios"]
        markdown = render_feedback_markdown(view)

        self.assertEqual(2, len(failed_scenarios))
        self.assertEqual("happy_path", failed_scenarios[0]["name"])
        self.assertIn("threshold_crossed", failed_scenarios[0]["failed_checks"])
        self.assertIn("oscillation detected (56 pump transitions, 85 samples)", failed_scenarios[0]["observations"])
        self.assertIn(
            "last valid sensor frame arrived at 300 ms and no timeout-driven OFF was observed",
            failed_scenarios[1]["observations"],
        )
        self.assertIn("Failed integration scenarios:", markdown)
        self.assertIn("happy_path: plant never crossed the upper threshold", markdown)
        self.assertIn("oscillation detected (56 pump transitions, 85 samples)", markdown)
        self.assertIn("last valid sensor frame arrived at 300 ms and no timeout-driven OFF was observed", markdown)

    def test_feedback_hides_passing_host_test_summary(self) -> None:
        view = project_feedback(
            {
                "task": {"task_id": "tank_fill_drain"},
                "stages": {
                    "host_tests": {
                        "success": True,
                        "returncode": 0,
                        "duration_s": 0.1,
                        "errors": ["100% tests passed, 0 tests failed out of 1"],
                    },
                },
                "summary": {"status": "PASS", "task_solved": True, "failure_category": "none"},
            },
            {"mode": "full"},
        )

        markdown = render_feedback_markdown(view)

        self.assertEqual([], view["tests"]["host_unit_tests"]["errors"])
        self.assertNotIn("Host unit test errors:", markdown)

    def test_feedback_hides_noisy_build_progress_on_success(self) -> None:
        view = project_feedback(
            {
                "task": {"task_id": "tank_fill_drain"},
                "stages": {
                    "build": {
                        "success": True,
                        "returncode": 0,
                        "duration_s": 1.0,
                        "errors": ["[27/1031] Building C object esp-idf/example/example.c.obj"],
                    },
                },
                "summary": {"status": "PASS", "task_solved": True, "failure_category": "none"},
            },
            {"mode": "full"},
        )

        markdown = render_feedback_markdown(view)

        self.assertEqual([], view["build"]["errors"])
        self.assertNotIn("Build errors:", markdown)

    def test_feedback_keeps_runtime_supplied_failed_scenario_observations(self) -> None:
        view = project_feedback(
            {
                "task": {"task_id": "thermal_chamber_hysteresis"},
                "stages": {
                    "integration": {
                        "success": False,
                        "returncode": 1,
                        "duration_s": 4.2,
                    },
                },
                "metrics": {
                    "integration": {
                        "scenarios": [
                            {
                                "name": "overshoot_guard",
                                "passed": False,
                                "reason": "temperature exceeded the hard upper limit of 56 C",
                                "checks": {"hard_limit_respected": False},
                                "observations": ["temperature peaked at 57 C above the hard limit of 56 C"],
                                "metrics": {
                                    "initial_temperature_c": 38,
                                    "min_temperature_c": 38,
                                    "max_temperature_c": 57,
                                    "final_temperature_c": 56,
                                    "heater_transitions": 2,
                                    "sample_count": 14,
                                },
                            }
                        ]
                    }
                },
                "summary": {"status": "INTEGRATION_FAILED", "task_solved": False, "failure_category": "overshoot_guard"},
            },
            {"mode": "full"},
        )

        failed_scenarios = view["tests"]["integration"]["failed_scenarios"]

        self.assertIn("temperature peaked at 57 C above the hard limit of 56 C", failed_scenarios[0]["observations"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
