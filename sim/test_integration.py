from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.scenarios import available_runtime, run_scenario
from sim.task_spec import load_task_spec


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "stage8"
DEFAULT_TASK_SPEC = load_task_spec(REPO_ROOT / "specs" / "tank_fill_drain.json")


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ready, reason = available_runtime(REPO_ROOT)
        if not ready:
            raise unittest.SkipTest(reason)

    def test_smoke(self) -> None:
        result = run_scenario("smoke", DEFAULT_ARTIFACT_ROOT / "smoke", task_spec=DEFAULT_TASK_SPEC, port=5555)
        self.assertTrue(result.passed, result.reason)

    def test_happy_path(self) -> None:
        result = run_scenario("happy_path", DEFAULT_ARTIFACT_ROOT / "happy_path", task_spec=DEFAULT_TASK_SPEC, port=5556)
        self.assertTrue(result.passed, result.reason)

    def test_sensor_timeout(self) -> None:
        result = run_scenario("sensor_timeout", DEFAULT_ARTIFACT_ROOT / "sensor_timeout", task_spec=DEFAULT_TASK_SPEC, port=5557)
        self.assertTrue(result.passed, result.reason)

    def test_malformed_frame(self) -> None:
        result = run_scenario("malformed_frame", DEFAULT_ARTIFACT_ROOT / "malformed_frame", task_spec=DEFAULT_TASK_SPEC, port=5558)
        self.assertTrue(result.passed, result.reason)


def _build_suite(keyword: str | None) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    test_names = [
        "test_smoke",
        "test_happy_path",
        "test_sensor_timeout",
        "test_malformed_frame",
    ]
    for test_name in test_names:
        if keyword and keyword not in test_name:
            continue
        suite.addTest(IntegrationTests(test_name))
    return suite


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the QEMU-backed integration tests.")
    parser.add_argument("-k", "--keyword", help="Only run tests whose name contains this substring.")
    args = parser.parse_args()

    result = unittest.TextTestRunner(verbosity=2).run(_build_suite(args.keyword))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
