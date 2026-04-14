from __future__ import annotations

import time
import subprocess
from dataclasses import dataclass
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

from .plant import TankPlant, TankPlantConfig


@dataclass(frozen=True)
class ScenarioSpec:
    name: str
    initial_level: int
    max_steps: int
    send_valid_until_ms: int | None = None
    inject_invalid_at_ms: int | None = None


def available_runtime(repo_root: Path) -> tuple[bool, str]:
    return shared_available_runtime(repo_root)


def scenario_specs(task_spec: TaskSpec | None = None) -> dict[str, ScenarioSpec]:
    return {
        "smoke": ScenarioSpec(name="smoke", initial_level=20, max_steps=8, send_valid_until_ms=0),
        "happy_path": ScenarioSpec(name="happy_path", initial_level=20, max_steps=28),
        "sensor_timeout": ScenarioSpec(name="sensor_timeout", initial_level=20, max_steps=22, send_valid_until_ms=300),
        "malformed_frame": ScenarioSpec(name="malformed_frame", initial_level=20, max_steps=10, send_valid_until_ms=0, inject_invalid_at_ms=100),
    }


def _plant_config(task_spec: TaskSpec) -> TankPlantConfig:
    payload = dict(task_spec.payload.get("plant", {}))
    sensor_range = task_spec.primary_sensor_range or (0, 100)
    return TankPlantConfig(
        tick_ms=int(payload.get("tick_ms", 100)),
        fill_delta=int(payload.get("fill_delta", 6)),
        drain_delta=int(payload.get("drain_delta", 1)),
        min_level=int(payload.get("min_level", sensor_range[0])),
        max_level=int(payload.get("max_level", sensor_range[1])),
    )


def _append_trace_sample(result: ScenarioResult, plant: TankPlant) -> None:
    sample = TraceSample(timestamp_ms=plant.now_ms, values={"level": plant.level, "pump_on": plant.pump_on})
    if result.trace_samples and result.trace_samples[-1] == sample:
        return
    result.trace_samples.append(sample)


def _record_firmware_lines(
    client: UartTcpClient,
    transcript: Transcript,
    plant: TankPlant,
    result: ScenarioResult,
    task_spec: TaskSpec,
    last_valid_send_monotonic: float | None,
) -> None:
    telemetry = result.telemetry
    for line in client.read_pending_lines():
        transcript.record(plant.now_ms / 1000.0, "fw->plant", line)
        if line == "DBG BOOTED":
            telemetry["saw_boot"] = True
            telemetry["firmware_ready"] = True
        if "main_task: Calling app_main()" in line or "main_task: Returned from app_main()" in line:
            telemetry["firmware_ready"] = True
        if line.startswith("ACT PUMP "):
            if line == "ACT PUMP ON":
                telemetry["saw_pump_on"] = True
            if line == "ACT PUMP OFF":
                telemetry["saw_pump_off"] = True
                if telemetry.get("threshold_cross_ms") is not None and plant.now_ms >= int(telemetry["threshold_cross_ms"]):
                    telemetry["off_after_threshold"] = True
                if telemetry.get("invalid_send_ms") is not None and plant.now_ms >= int(telemetry["invalid_send_ms"]):
                    telemetry["safe_off_after_invalid"] = True
                if last_valid_send_monotonic is not None and telemetry.get("timeout_off_ms") is None:
                    elapsed_ms = int(round((time.monotonic() - last_valid_send_monotonic) * 1000.0))
                    if elapsed_ms >= task_spec.timeout_bounds_ms[0]:
                        telemetry["timeout_off_ms"] = plant.now_ms
                        telemetry["timeout_off_delta_ms"] = elapsed_ms
            if telemetry.get("last_valid_send_ms") is not None or telemetry.get("invalid_send_ms") is not None:
                telemetry["saw_exchange"] = True
            plant.apply_firmware_line(line)
            _append_trace_sample(result, plant)


def _should_send_valid_frame(spec: ScenarioSpec, plant: TankPlant) -> bool:
    if spec.name == "malformed_frame" and plant.now_ms > 0:
        return False
    if spec.send_valid_until_ms is None:
        return True
    return plant.now_ms <= spec.send_valid_until_ms


def _scenario_goal_reached(spec_name: str, telemetry: dict[str, object]) -> bool:
    if spec_name == "smoke":
        return bool(telemetry.get("saw_exchange", False))
    if spec_name == "happy_path":
        return bool(telemetry.get("saw_pump_on", False) and telemetry.get("off_after_threshold", False))
    if spec_name == "sensor_timeout":
        return bool(telemetry.get("saw_pump_on", False) and telemetry.get("timeout_off_delta_ms") is not None)
    if spec_name == "malformed_frame":
        return bool(telemetry.get("safe_off_after_invalid", False))
    return False


def _settling_time_ms(samples: list[TraceSample], band_min: int, band_max: int) -> int | None:
    for index, sample in enumerate(samples):
        if all(band_min <= int(later.values["level"]) <= band_max for later in samples[index:]):
            return sample.timestamp_ms
    return None


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
            "steady_state_error": None,
            "overshoot": None,
            "undershoot": None,
            "rise_time_ms": None,
            "settling_time_ms": None,
            "oscillation_detected": True,
            "pump_transitions": None,
            "pump_full_scale_ratio": None,
            "time_to_first_valid_actuation_ms": None,
            "constraint_violations": None,
            "no_progress_detected": True,
        }

    band_min, band_max = task_spec.target_band
    plant_min, plant_max = task_spec.primary_sensor_range or (0, 100)
    levels = [int(sample.values["level"]) for sample in samples]
    pump_states = [bool(sample.values.get("pump_on", False)) for sample in samples]
    switch_count = _count_transitions(samples, "pump_on")

    initial_pump_state = pump_states[0]
    first_actuation = next(
        (sample.timestamp_ms for sample in samples if bool(sample.values.get("pump_on", False)) != initial_pump_state),
        None,
    )
    rise_time_ms = next((sample.timestamp_ms for sample in samples if int(sample.values["level"]) >= band_min), None)
    settling_time_ms = _settling_time_ms(samples, band_min, band_max)
    constraint_violations = sum(1 for level in levels if level < plant_min or level > plant_max)

    return {
        "sample_count": len(samples),
        "initial_level": levels[0],
        "final_level": levels[-1],
        "min_level": min(levels),
        "max_level": max(levels),
        "steady_state_error": abs(levels[-1] - task_spec.target_band_center),
        "overshoot": max(0, max(levels) - band_max),
        "undershoot": max(0, band_min - min(levels)),
        "rise_time_ms": rise_time_ms,
        "settling_time_ms": settling_time_ms,
        "oscillation_detected": switch_count > 2,
        "pump_transitions": switch_count,
        "pump_full_scale_ratio": sum(1 for state in pump_states if state) / float(len(samples)),
        "time_to_first_valid_actuation_ms": first_actuation,
        "constraint_violations": constraint_violations,
        "no_progress_detected": len(set(levels)) <= 1,
        "duration_ms": samples[-1].timestamp_ms,
    }


def _evaluate_result(result: ScenarioResult, task_spec: TaskSpec) -> None:
    telemetry = result.telemetry
    metrics = _compute_trace_metrics(result.trace_samples, task_spec)
    timeout_min_ms, timeout_max_ms = task_spec.timeout_bounds_ms
    checks: dict[str, object] = {
        "firmware_ready": telemetry.get("firmware_ready", False),
        "saw_exchange": telemetry.get("saw_exchange", False),
        "runtime_timeout": telemetry.get("runtime_timeout", False),
    }
    observations: list[str] = []

    if not checks["firmware_ready"]:
        result.passed = False
        result.reason = "firmware never reached app_main readiness"
    elif telemetry.get("runtime_timeout", False):
        result.passed = False
        result.reason = "scenario timed out before the required behavior was observed"
    elif telemetry.get("qemu_return_code") not in {None, 0} and not telemetry.get("allow_nonzero_exit", False):
        result.passed = False
        result.reason = f"QEMU exited early with code {telemetry['qemu_return_code']}"
    elif result.name == "smoke":
        result.passed = bool(telemetry.get("saw_exchange", False))
        result.reason = "received at least one actuator frame" if result.passed else "no actuator response observed"
    elif result.name == "happy_path":
        checks.update(
            {
                "saw_pump_on": telemetry.get("saw_pump_on", False),
                "off_after_threshold": telemetry.get("off_after_threshold", False),
                "threshold_crossed": telemetry.get("threshold_cross_ms") is not None,
            }
        )
        if not checks["saw_pump_on"]:
            result.passed = False
            result.reason = "controller never turned the pump on"
        elif not checks["threshold_crossed"]:
            result.passed = False
            result.reason = "plant never crossed the upper threshold"
        elif not checks["off_after_threshold"]:
            result.passed = False
            result.reason = "controller never turned the pump off after crossing the upper threshold"
        else:
            result.passed = True
            result.reason = "saw ON/OFF transitions across the safe band"
    elif result.name == "sensor_timeout":
        timeout_delta = telemetry.get("timeout_off_delta_ms")
        checks.update(
            {
                "saw_pump_on": telemetry.get("saw_pump_on", False),
                "timeout_off_detected": timeout_delta is not None,
                "timeout_off_delta_ms": timeout_delta,
            }
        )
        if not checks["saw_pump_on"]:
            result.passed = False
            result.reason = "controller never entered the pumping state"
        elif timeout_delta is None:
            result.passed = False
            result.reason = "timeout-driven PUMP OFF was not observed"
        elif int(timeout_delta) < timeout_min_ms or int(timeout_delta) > timeout_max_ms:
            result.passed = False
            result.reason = f"timeout off bound violated: {timeout_delta} ms"
        else:
            result.passed = True
            result.reason = "timeout forced a bounded safe-off transition"
    elif result.name == "malformed_frame":
        checks["safe_off_after_invalid"] = telemetry.get("safe_off_after_invalid", False)
        result.passed = bool(checks["safe_off_after_invalid"])
        result.reason = (
            "malformed input triggered safe-off behavior"
            if result.passed
            else "malformed input did not produce a safe-off response"
        )
    else:
        result.passed = False
        result.reason = f"unknown scenario {result.name}"

    if result.name == "happy_path" and metrics.get("no_progress_detected"):
        observations.append("the tank never moved away from its initial level")
    if result.name == "sensor_timeout" and telemetry.get("last_valid_send_ms") is not None and telemetry.get("timeout_off_delta_ms") is None:
        observations.append("valid sensor frames stopped, but no timeout-driven pump-off transition was observed")

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
    plant = TankPlant(level=spec.initial_level, config=_plant_config(task_spec))
    result = ScenarioResult(
        name=spec.name,
        passed=False,
        reason="scenario did not finish",
        telemetry={
            "firmware_ready": False,
            "saw_boot": False,
            "saw_exchange": False,
            "saw_pump_on": False,
            "saw_pump_off": False,
            "off_after_threshold": False,
            "safe_off_after_invalid": False,
            "threshold_cross_ms": None,
            "timeout_off_ms": None,
            "timeout_off_delta_ms": None,
            "last_valid_send_ms": None,
            "invalid_send_ms": None,
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

                if _should_send_valid_frame(spec, plant):
                    payload = plant.sense_frame()
                    client.send_line(payload)
                    transcript.record(plant.now_ms / 1000.0, "plant->fw", payload)
                    result.telemetry["last_valid_send_ms"] = plant.now_ms
                    last_valid_send_monotonic = time.monotonic()

                if spec.inject_invalid_at_ms is not None and plant.now_ms == spec.inject_invalid_at_ms:
                    payload = "SENSE LEVEL banana"
                    client.send_line(payload)
                    transcript.record(plant.now_ms / 1000.0, "plant->fw", payload)
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
                if result.telemetry.get("threshold_cross_ms") is None and plant.level > task_spec.target_band[1]:
                    result.telemetry["threshold_cross_ms"] = plant.now_ms
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
