from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.test_evaluator import EvaluatorTests
from sim.test_feedback import FeedbackTests
from sim.plant import TankPlant
from sim.test_plant import (
    FilterTankPlantTests,
    MixingTankPlantTests,
    PressureVesselPlantTests,
    TankPlantTests,
    ThermalChamberPlantTests,
)
from sim.test_registry import RegistryTests
from sim.test_task_spec import TaskSpecTests
from sim.test_visible_run_eval import VisibleRunEvalTests
from sim.transcript import Transcript


def _sample_transcript() -> Transcript:
    plant = TankPlant(level=20)
    transcript = Transcript()

    transcript.record(0.0, "harness", "START plant sample")
    for _ in range(8):
        transcript.record(plant.now_ms / 1000.0, "plant->fw", plant.sense_frame())
        if plant.level < 30:
            plant.apply_firmware_line("ACT PUMP ON")
            transcript.record(plant.now_ms / 1000.0, "fw->plant", "ACT PUMP ON")
        elif plant.level > 80:
            plant.apply_firmware_line("ACT PUMP OFF")
            transcript.record(plant.now_ms / 1000.0, "fw->plant", "ACT PUMP OFF")
        plant.step()
    transcript.record(plant.now_ms / 1000.0, "harness", "STOP plant sample")
    return transcript


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    artifact_dir = repo_root / "artifacts" / "stage6"
    log_file = artifact_dir / "plant_unit_tests.log"
    transcript_file = artifact_dir / "sample_transcript.log"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    stream = io.StringIO()
    suite = unittest.TestSuite()
    for case in (
        TankPlantTests,
        ThermalChamberPlantTests,
        PressureVesselPlantTests,
        MixingTankPlantTests,
        FilterTankPlantTests,
        RegistryTests,
        TaskSpecTests,
        VisibleRunEvalTests,
        EvaluatorTests,
        FeedbackTests,
    ):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    log_file.write_text(stream.getvalue(), encoding="ascii")
    _sample_transcript().write(transcript_file)

    print(stream.getvalue(), end="")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
