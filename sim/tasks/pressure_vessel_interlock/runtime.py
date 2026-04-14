from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from sim.evaluator import write_json, write_trace_csv
from sim.qemu_runtime import (
    ConnectionClosedError,
    UartTcpClient,
    available_runtime as shared_available_runtime,
    start_qemu,
    wait_for_uart,
)
from sim.task_spec import TaskSpec
from sim.tasks.base import ScenarioResult, TraceSample
from sim.transcript import Transcript


@dataclass(frozen=True)
class ScenarioSpec:
    name: str
    initial_pressure_kpa: int
    max_steps: int
    initial_door_closed: bool = True
    send_valid_until_ms: int | None = None
    invalid_at_ms: int | None = None
    invalid_frame: str | None = None
    door_events: dict[int, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class PressureVesselPlantConfig:
    tick_ms: int = 100
    compressor_gain_kpa: int = 10
    vent_relief_kpa: int = 14
    natural_leak_kpa: int = 2
    door_relief_kpa: int = 10
    min_pressure_kpa: int = 0
    max_pressure_kpa: int = 120


@dataclass
class PressureVesselPlant:
    pressure_kpa: int
    door_closed: bool = True
    compressor_on: bool = False
    vent_open: bool = True
    now_ms: int = 0
    config: PressureVesselPlantConfig = field(default_factory=PressureVesselPlantConfig)

    def sense_pressure_frame(self) -> str:
        return f"SENSE PRESS {self.pressure_kpa}"

    def sense_door_frame(self) -> str:
        return "SENSE DOOR CLOSED" if self.door_closed else "SENSE DOOR OPEN"

    def apply_firmware_line(self, line: str) -> bool:
        normalized = line.strip()
        if normalized == "ACT COMPRESSOR ON":
            self.compressor_on = True
            return True
        if normalized == "ACT COMPRESSOR OFF":
            self.compressor_on = False
            return True
        if normalized == "ACT VENT OPEN":
            self.vent_open = True
            return True
        if normalized == "ACT VENT CLOSED":
            self.vent_open = False
            return True
        return False

    def step(self) -> int:
        delta = -self.config.natural_leak_kpa
        if self.vent_open:
            delta -= self.config.vent_relief_kpa
        if not self.door_closed:
            delta -= self.config.door_relief_kpa
        if self.compressor_on and self.door_closed and not self.vent_open:
            delta += self.config.compressor_gain_kpa

        self.pressure_kpa = max(
            self.config.min_pressure_kpa,
            min(self.config.max_pressure_kpa, self.pressure_kpa + delta),
        )
        self.now_ms += self.config.tick_ms
        return self.pressure_kpa


def available_runtime(repo_root: Path) -> tuple[bool, str]:
    return shared_available_runtime(repo_root)


def scenario_specs(task_spec: TaskSpec | None = None) -> dict[str, ScenarioSpec]:
    return {
        "smoke": ScenarioSpec(name="smoke", initial_pressure_kpa=20, max_steps=6, send_valid_until_ms=0),
        "pressurize_control": ScenarioSpec(name="pressurize_control", initial_pressure_kpa=18, max_steps=22),
        "relief_control": ScenarioSpec(name="relief_control", initial_pressure_kpa=78, max_steps=12),
        "door_open_interlock": ScenarioSpec(
            name="door_open_interlock",
            initial_pressure_kpa=25,
            max_steps=18,
            door_events={300: False},
        ),
        "sensor_timeout": ScenarioSpec(
            name="sensor_timeout",
            initial_pressure_kpa=20,
            max_steps=18,
            send_valid_until_ms=300,
        ),
        "malformed_frame": ScenarioSpec(
            name="malformed_frame",
            initial_pressure_kpa=44,
            max_steps=10,
            send_valid_until_ms=0,
            invalid_at_ms=100,
            invalid_frame="SENSE DOOR AJAR",
        ),
    }


def _plant_config(task_spec: TaskSpec) -> PressureVesselPlantConfig:
    payload = dict(task_spec.payload.get("plant", {}))
    sensor_range = task_spec.primary_sensor_range or (0, 120)
    return PressureVesselPlantConfig(
        tick_ms=int(payload.get("tick_ms", 100)),
        compressor_gain_kpa=int(payload.get("compressor_gain_kpa", 10)),
        vent_relief_kpa=int(payload.get("vent_relief_kpa", 14)),
        natural_leak_kpa=int(payload.get("natural_leak_kpa", 2)),
        door_relief_kpa=int(payload.get("door_relief_kpa", 10)),
        min_pressure_kpa=int(payload.get("min_pressure_kpa", sensor_range[0])),
        max_pressure_kpa=int(payload.get("max_pressure_kpa", sensor_range[1])),
    )


def _append_trace_sample(result: ScenarioResult, plant: PressureVesselPlant) -> None:
    sample = TraceSample(
        timestamp_ms=plant.now_ms,
        values={
            "pressure_kpa": plant.pressure_kpa,
            "door_closed": plant.door_closed,
            "compressor_on": plant.compressor_on,
            "vent_open": plant.vent_open,
        },
    )
    if result.trace_samples and result.trace_samples[-1] == sample:
        return
    result.trace_samples.append(sample)


def _record_firmware_lines(
    client: UartTcpClient,
    transcript: Transcript,
    plant: PressureVesselPlant,
    result: ScenarioResult,
    task_spec: TaskSpec,
    last_valid_send_monotonic: float | None,
) -> None:
    telemetry = result.telemetry
    actuator_lines: list[str] = []
    saw_new_actuator = False

    for line in client.read_pending_lines():
        transcript.record(plant.now_ms / 1000.0, "fw->plant", line)
        if line == "DBG BOOTED":
            telemetry["saw_boot"] = True
            telemetry["firmware_ready"] = True
        if "main_task: Calling app_main()" in line or "main_task: Returned from app_main()" in line:
            telemetry["firmware_ready"] = True
        if line.startswith("ACT COMPRESSOR ") or line.startswith("ACT VENT "):
            saw_new_actuator = True
            actuator_lines.append(line)
            if line == "ACT COMPRESSOR ON":
                telemetry["saw_compressor_on"] = True
            elif line == "ACT COMPRESSOR OFF":
                telemetry["saw_compressor_off"] = True
            elif line == "ACT VENT OPEN":
                telemetry["saw_vent_open"] = True
            elif line == "ACT VENT CLOSED":
                telemetry["saw_vent_closed"] = True

    if not actuator_lines:
        return

    for line in actuator_lines:
        plant.apply_firmware_line(line)

    if telemetry.get("last_valid_send_ms") is not None or telemetry.get("invalid_send_ms") is not None:
        telemetry["saw_exchange"] = True

    if plant.compressor_on and plant.vent_open:
        telemetry["mutual_exclusion_violations"] = int(telemetry.get("mutual_exclusion_violations", 0)) + 1

    if (
        telemetry.get("door_open_ms") is not None
        and plant.now_ms >= int(telemetry["door_open_ms"])
        and (not plant.compressor_on)
        and plant.vent_open
    ):
        telemetry["safe_after_door_open"] = True

    if (
        telemetry.get("invalid_send_ms") is not None
        and plant.now_ms >= int(telemetry["invalid_send_ms"])
        and (not plant.compressor_on)
        and plant.vent_open
    ):
        telemetry["safe_after_invalid"] = True

    if last_valid_send_monotonic is not None and telemetry.get("timeout_safe_delta_ms") is None:
        elapsed_ms = int(round((time.monotonic() - last_valid_send_monotonic) * 1000.0))
        if elapsed_ms >= task_spec.timeout_bounds_ms[0] and (not plant.compressor_on) and plant.vent_open:
            telemetry["timeout_safe_ms"] = plant.now_ms
            telemetry["timeout_safe_delta_ms"] = elapsed_ms

    if saw_new_actuator:
        _append_trace_sample(result, plant)


def _should_send_valid_frame(spec: ScenarioSpec, plant: PressureVesselPlant) -> bool:
    if spec.name == "malformed_frame" and plant.now_ms > 0:
        return False
    if spec.send_valid_until_ms is None:
        return True
    return plant.now_ms <= spec.send_valid_until_ms


def _scenario_goal_reached(spec_name: str, telemetry: dict[str, object]) -> bool:
    if spec_name == "smoke":
        return bool(telemetry.get("saw_exchange", False))
    if spec_name == "pressurize_control":
        return bool(telemetry.get("entered_target_band_ms") is not None)
    if spec_name == "relief_control":
        return bool(telemetry.get("relieved_after_threshold", False))
    if spec_name == "door_open_interlock":
        return bool(telemetry.get("safe_after_door_open", False))
    if spec_name == "sensor_timeout":
        return telemetry.get("timeout_safe_delta_ms") is not None
    if spec_name == "malformed_frame":
        return bool(telemetry.get("safe_after_invalid", False))
    return False


def _count_transitions(samples: list[TraceSample], key: str) -> int:
    transitions = 0
    previous = None
    for sample in samples:
        current = bool(sample.values.get(key, False))
        if previous is not None and current != previous:
            transitions += 1
        previous = current
    return transitions


def _compute_trace_metrics(samples: list[TraceSample], task_spec: TaskSpec) -> dict[str, object]:
    if not samples:
        return {
            "sample_count": 0,
            "min_pressure_kpa": None,
            "max_pressure_kpa": None,
            "final_pressure_kpa": None,
            "entered_target_band_ms": None,
            "compressor_transitions": None,
            "vent_transitions": None,
            "constraint_violations": None,
            "mutual_exclusion_violations": None,
            "duration_ms": None,
            "no_progress_detected": True,
        }

    band_min, band_max = task_spec.target_band
    plant_min, plant_max = task_spec.primary_sensor_range or (0, 120)
    pressures = [int(sample.values["pressure_kpa"]) for sample in samples]
    entered_target_band_ms = next(
        (sample.timestamp_ms for sample in samples if band_min <= int(sample.values["pressure_kpa"]) <= band_max),
        None,
    )
    return {
        "sample_count": len(samples),
        "min_pressure_kpa": min(pressures),
        "max_pressure_kpa": max(pressures),
        "final_pressure_kpa": pressures[-1],
        "entered_target_band_ms": entered_target_band_ms,
        "compressor_transitions": _count_transitions(samples, "compressor_on"),
        "vent_transitions": _count_transitions(samples, "vent_open"),
        "constraint_violations": sum(1 for value in pressures if value < plant_min or value > plant_max),
        "mutual_exclusion_violations": sum(
            1
            for sample in samples
            if bool(sample.values.get("compressor_on", False)) and bool(sample.values.get("vent_open", False))
        ),
        "duration_ms": samples[-1].timestamp_ms,
        "no_progress_detected": len(set(pressures)) <= 1,
    }


def _evaluate_result(result: ScenarioResult, task_spec: TaskSpec) -> None:
    telemetry = result.telemetry
    metrics = _compute_trace_metrics(result.trace_samples, task_spec)
    timeout_min_ms, timeout_max_ms = task_spec.timeout_bounds_ms
    checks: dict[str, object] = {
        "firmware_ready": telemetry.get("firmware_ready", False),
        "saw_exchange": telemetry.get("saw_exchange", False),
        "runtime_timeout": telemetry.get("runtime_timeout", False),
        "mutual_exclusion_respected": int(metrics.get("mutual_exclusion_violations", 0) or 0) == 0,
    }
    observations: list[str] = []

    if not checks["firmware_ready"]:
        result.passed = False
        result.reason = "firmware never reached app_main readiness"
    elif telemetry.get("runtime_timeout", False):
        result.passed = False
        result.reason = "scenario timed out before the required behavior was observed"
    elif telemetry.get("qemu_return_code") not in {None, 0}:
        result.passed = False
        result.reason = f"QEMU exited early with code {telemetry['qemu_return_code']}"
    elif result.name == "smoke":
        result.passed = bool(telemetry.get("saw_exchange", False))
        result.reason = "received actuator output" if result.passed else "no actuator output observed"
    elif result.name == "pressurize_control":
        checks["saw_compressor_on"] = telemetry.get("saw_compressor_on", False)
        checks["entered_target_band"] = metrics.get("entered_target_band_ms") is not None
        if not checks["saw_compressor_on"]:
            result.passed = False
            result.reason = "controller never turned the compressor on"
        elif not checks["entered_target_band"]:
            result.passed = False
            result.reason = "pressure never entered the working band"
        elif not checks["mutual_exclusion_respected"]:
            result.passed = False
            result.reason = "compressor and vent were active together"
        else:
            result.passed = True
            result.reason = "pressurized into the band without violating the interlock"
    elif result.name == "relief_control":
        checks["saw_vent_open"] = telemetry.get("saw_vent_open", False)
        checks["relieved_after_threshold"] = telemetry.get("relieved_after_threshold", False)
        if not checks["saw_vent_open"]:
            result.passed = False
            result.reason = "controller never opened the vent"
        elif not checks["relieved_after_threshold"]:
            result.passed = False
            result.reason = "pressure did not return below the upper threshold"
        elif not checks["mutual_exclusion_respected"]:
            result.passed = False
            result.reason = "compressor and vent were active together"
        else:
            result.passed = True
            result.reason = "venting reduced pressure back below the upper threshold"
    elif result.name == "door_open_interlock":
        checks["saw_compressor_on"] = telemetry.get("saw_compressor_on", False)
        checks["safe_after_door_open"] = telemetry.get("safe_after_door_open", False)
        if not checks["saw_compressor_on"]:
            result.passed = False
            result.reason = "controller never entered the pressurizing state"
        elif not checks["safe_after_door_open"]:
            result.passed = False
            result.reason = "door-open event did not force the safe vented state"
        elif not checks["mutual_exclusion_respected"]:
            result.passed = False
            result.reason = "compressor and vent were active together"
        else:
            result.passed = True
            result.reason = "door-open event forced a safe vented transition"
    elif result.name == "sensor_timeout":
        timeout_delta = telemetry.get("timeout_safe_delta_ms")
        checks["saw_compressor_on"] = telemetry.get("saw_compressor_on", False)
        checks["timeout_safe_delta_ms"] = timeout_delta
        if not checks["saw_compressor_on"]:
            result.passed = False
            result.reason = "controller never pressurized before sensor loss"
        elif timeout_delta is None:
            result.passed = False
            result.reason = "timeout-driven safe venting was not observed"
        elif int(timeout_delta) < timeout_min_ms or int(timeout_delta) > timeout_max_ms:
            result.passed = False
            result.reason = f"timeout reaction bound violated: {timeout_delta} ms"
        else:
            result.passed = True
            result.reason = "sensor timeout forced a bounded safe vented state"
    elif result.name == "malformed_frame":
        checks["safe_after_invalid"] = telemetry.get("safe_after_invalid", False)
        result.passed = bool(checks["safe_after_invalid"])
        result.reason = (
            "malformed input triggered the safe vented state"
            if result.passed
            else "malformed input did not trigger the safe vented state"
        )
    else:
        result.passed = False
        result.reason = f"unknown scenario {result.name}"

    if not checks["mutual_exclusion_respected"]:
        observations.append("compressor and vent were observed active together in a stable sample")
    if metrics.get("no_progress_detected"):
        observations.append("pressure never moved away from its initial value")
    if result.name == "sensor_timeout" and telemetry.get("last_valid_send_ms") is not None and telemetry.get("timeout_safe_delta_ms") is None:
        observations.append("sensor frames stopped, but no bounded safe vent transition was observed")

    result.checks = checks
    result.metrics = metrics
    result.observations = observations


def run_scenario(
    name: str,
    artifact_dir: Path,
    task_spec: TaskSpec,
    port: int = 5555,
    timeout_s: float = 20.0,
) -> ScenarioResult:
    repo_root = Path(__file__).resolve().parents[3]
    ready, reason = available_runtime(repo_root)
    if not ready:
        raise RuntimeError(reason)

    specs = scenario_specs(task_spec)
    if name not in specs:
        available = ", ".join(sorted(specs.keys()))
        raise ValueError(f"unknown scenario for {task_spec.task_id}: {name}. available scenarios: {available}")

    spec = specs[name]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    transcript = Transcript()
    plant = PressureVesselPlant(
        pressure_kpa=spec.initial_pressure_kpa,
        door_closed=spec.initial_door_closed,
        config=_plant_config(task_spec),
    )
    result = ScenarioResult(
        name=spec.name,
        passed=False,
        reason="scenario did not finish",
        telemetry={
            "firmware_ready": False,
            "saw_boot": False,
            "saw_exchange": False,
            "saw_compressor_on": False,
            "saw_compressor_off": False,
            "saw_vent_open": False,
            "saw_vent_closed": False,
            "entered_target_band_ms": None,
            "relieved_after_threshold": False,
            "door_open_ms": None,
            "safe_after_door_open": False,
            "timeout_safe_ms": None,
            "timeout_safe_delta_ms": None,
            "safe_after_invalid": False,
            "last_valid_send_ms": None,
            "invalid_send_ms": None,
            "mutual_exclusion_violations": 0,
            "runtime_timeout": False,
            "qemu_return_code": None,
        },
    )
    last_valid_send_monotonic: float | None = None

    transcript.record(0.0, "harness", f"START qemu scenario={spec.name}")
    _append_trace_sample(result, plant)
    process, stdout_handle, stderr_handle = start_qemu(repo_root, artifact_dir, port)
    client: UartTcpClient | None = None
    process_exited_on_its_own = False

    try:
        client = wait_for_uart(port=port, deadline=time.monotonic() + 5.0, artifact_dir=artifact_dir)
        transcript.record(0.0, "harness", f"CONNECTED tcp:{port}")
        boot_deadline = time.monotonic() + 2.0
        while time.monotonic() < boot_deadline and not result.telemetry.get("firmware_ready", False):
            _record_firmware_lines(client, transcript, plant, result, task_spec, last_valid_send_monotonic)
            time.sleep(0.01)

        overall_deadline = time.monotonic() + timeout_s
        if result.telemetry.get("firmware_ready", False):
            for _ in range(spec.max_steps):
                if time.monotonic() >= overall_deadline:
                    result.telemetry["runtime_timeout"] = True
                    break

                if plant.now_ms in spec.door_events:
                    plant.door_closed = spec.door_events[plant.now_ms]
                    if not plant.door_closed and result.telemetry.get("door_open_ms") is None:
                        result.telemetry["door_open_ms"] = plant.now_ms

                if _should_send_valid_frame(spec, plant):
                    for payload in (plant.sense_pressure_frame(), plant.sense_door_frame()):
                        client.send_line(payload)
                        transcript.record(plant.now_ms / 1000.0, "plant->fw", payload)
                    result.telemetry["last_valid_send_ms"] = plant.now_ms
                    last_valid_send_monotonic = time.monotonic()

                if spec.invalid_at_ms is not None and spec.invalid_frame and plant.now_ms == spec.invalid_at_ms:
                    client.send_line(spec.invalid_frame)
                    transcript.record(plant.now_ms / 1000.0, "plant->fw", spec.invalid_frame)
                    result.telemetry["invalid_send_ms"] = plant.now_ms

                deadline = time.monotonic() + 0.15
                while time.monotonic() < deadline:
                    _record_firmware_lines(client, transcript, plant, result, task_spec, last_valid_send_monotonic)
                    time.sleep(0.01)

                if process.poll() is not None:
                    process_exited_on_its_own = True
                    break

                if _scenario_goal_reached(spec.name, result.telemetry):
                    break

                plant.step()
                if (
                    result.telemetry.get("entered_target_band_ms") is None
                    and task_spec.target_band[0] <= plant.pressure_kpa <= task_spec.target_band[1]
                ):
                    result.telemetry["entered_target_band_ms"] = plant.now_ms
                if plant.pressure_kpa <= task_spec.target_band[1] and spec.initial_pressure_kpa > task_spec.target_band[1]:
                    result.telemetry["relieved_after_threshold"] = True
                _append_trace_sample(result, plant)
    except (ConnectionClosedError, TimeoutError) as exc:
        transcript.record(plant.now_ms / 1000.0, "harness", f"ERROR {exc}")
    finally:
        if client is not None:
            client._sock.close()
        if process.poll() is not None:
            process_exited_on_its_own = True
        if not process_exited_on_its_own:
            process.terminate()
            try:
                process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5.0)

        result.telemetry["qemu_return_code"] = process.returncode if process_exited_on_its_own else None
        transcript.record(
            plant.now_ms / 1000.0,
            "harness",
            f"STOP qemu status={result.telemetry['qemu_return_code'] if process_exited_on_its_own else 'terminated_by_harness'}",
        )

        stdout_handle.close()
        stderr_handle.close()

        _evaluate_result(result, task_spec)
        transcript.write(artifact_dir / "transcript.log")
        write_trace_csv(artifact_dir / "trace.csv", result.trace_samples)
        write_json(artifact_dir / "metrics.json", result.metrics)
        write_json(artifact_dir / "summary.json", result.to_json())

    return result


def run_many(
    names: Iterable[str],
    artifact_root: Path,
    task_spec: TaskSpec,
    port: int = 5555,
) -> list[ScenarioResult]:
    results: list[ScenarioResult] = []
    for index, name in enumerate(names):
        results.append(run_scenario(name, artifact_root / name, task_spec=task_spec, port=port + index))
    return results
