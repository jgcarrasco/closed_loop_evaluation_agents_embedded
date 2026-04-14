from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.tasks.tank_fill_drain.plant import TankPlant, TankPlantConfig
from sim.transcript import Transcript


def _run_demo(steps: int) -> str:
    plant = TankPlant(level=20)
    transcript = Transcript()

    transcript.record(0.0, "harness", "START plant demo")
    for _ in range(steps):
        transcript.record(plant.now_ms / 1000.0, "plant->fw", plant.sense_frame())
        if plant.level < 30:
            plant.apply_firmware_line("ACT PUMP ON")
            transcript.record(plant.now_ms / 1000.0, "fw->plant", "ACT PUMP ON")
        elif plant.level > 80:
            plant.apply_firmware_line("ACT PUMP OFF")
            transcript.record(plant.now_ms / 1000.0, "fw->plant", "ACT PUMP OFF")
        plant.step()

    return "\n".join(event.render() for event in transcript.events)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a deterministic tank-plant demo.")
    parser.add_argument("--steps", type=int, default=12, help="Number of 100 ms steps to simulate.")
    args = parser.parse_args()

    print(_run_demo(args.steps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
