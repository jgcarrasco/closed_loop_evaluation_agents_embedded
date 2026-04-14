from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.scenarios import run_scenario
from sim.task_spec import load_task_spec


DEFAULT_TASK_SPEC = Path(__file__).resolve().parents[1] / "specs" / "tank_fill_drain.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the smoke integration scenario.")
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts/stage7"), help="Directory for smoke-test artifacts.")
    parser.add_argument("--port", type=int, default=5555, help="TCP port that QEMU should expose for UART.")
    parser.add_argument(
        "--task-spec",
        type=Path,
        default=DEFAULT_TASK_SPEC,
        help="Structured task specification used for metrics and pass/fail thresholds.",
    )
    args = parser.parse_args()

    try:
        result = run_scenario("smoke", args.artifact_dir, task_spec=load_task_spec(args.task_spec), port=args.port, timeout_s=10.0)
    except RuntimeError as exc:
        print(json.dumps({"scenario": "smoke", "error": str(exc)}, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result.to_json(), indent=2, sort_keys=True))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
