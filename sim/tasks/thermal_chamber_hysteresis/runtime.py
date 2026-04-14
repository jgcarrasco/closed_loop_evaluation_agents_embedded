from __future__ import annotations

import time
import subprocess
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
    initial_temperature_c: int
    max_steps: int
    initial_retained_heat_c: int = 0
    send_valid_until_ms: int | None = None
    inject_invalid_at_ms: int | None = None


@dataclass(frozen=True)
class ThermalChamberPlantConfig:
    tick_ms: int = 100
    ambient_temp_c: int = 24
    heater_gain_c: int = 3
    passive_cooling_c: int = 1
    retained_heat_gain_c: int = 2
    retained_heat_decay_c: int = 1
    max_retained_heat_c: int = 6
    min_temp_c: int = 15
    max_temp_c: int = 80


@dataclass
class ThermalChamberPlant:
    temperature_c: int
    heater_on: bool = False
    retained_heat_c: int = 0
    now_ms: int = 0
    config: ThermalChamberPlantConfig = field(default_factory=ThermalChamberPlantConfig)

    def sense_frame(self) -> str:
        return f"SENSE TEMP {self.temperature_c}"

    def apply_firmware_line(self, line: str) -> bool:
        normalized = line.strip()
        if normalized == "ACT HEATER ON":
            self.heater_on = True
            return True
        if normalized == "ACT HEATER OFF":
            self.heater_on = False
            return True
        return False

    def step(self) -> int:
        if self.heater_on:
            self.retained_heat_c = min(
                self.config.max_retained_heat_c,
                self.retained_heat_c + self.config.retained_heat_gain_c,
            )
        else:
            self.retained_heat_c = max(0, self.retained_heat_c - self.config.retained_heat_decay_c)

        delta = (self.config.heater_gain_c if self.heater_on else 0) + (self.retained_heat_c // 2)
        if self.temperature_c > self.config.ambient_temp_c:
            delta -= self.config.passive_cooling_c

        self.temperature_c = max(
            self.config.min_temp_c,
            min(self.config.max_temp_c, self.temperature_c + delta),
        )
        self.now_ms += self.config.tick_ms
        return self.temperature_c


def available_runtime(repo_root: Path) -> tuple[bool, str]:
    return shared_available_runtime(repo_root)


def scenario_specs(task_spec: TaskSpec | None = None) -> dict[str, ScenarioSpec]:
    return {
        "smoke": ScenarioSpec(name="smoke", initial_temperature_c=24, max_steps=8, send_valid_until_ms=0),
        "warmup_control": ScenarioSpec(name="warmup_control", initial_temperature_c=28, max_steps=24),
        "overshoot_guard": ScenarioSpec(name="overshoot_guard", initial_temperature_c=38, max_steps=18),
        "sensor_timeout": ScenarioSpec(name="sensor_timeout", initial_temperature_c=38, max_steps=18, send_valid_until_ms=300),
        "malformed_frame": ScenarioSpec(name="malformed_frame", initial_temperature_c=45, max_steps=10, send_valid_until_ms=0, inject_invalid_at_ms=100),
    }


def _plant_config(task_spec: TaskSpec) -> ThermalChamberPlantConfig:
    payload = dict(task_spec.payload.get("plant", {}))
    sensor_range = task_spec.primary_sensor_range or (15, 80)
    return ThermalChamberPlantConfig(
        tick_ms=int(payload.get("tick_ms", 100)),
        ambient_temp_c=int(payload.get("ambient_temp_c", 24)),
        heater_gain_c=int(payload.get("heater_gain_c", 3)),
        passive_cooling_c=int(payload.get("passive_cooling_c", 1)),
        retained_heat_gain_c=int(payload.get("retained_heat_gain_c", 2)),
        retained_heat_decay_c=int(payload.get("retained_heat_decay_c", 1)),
        max_retained_heat_c=int(payload.get("max_retained_heat_c", 6)),
        min_temp_c=int(payload.get("min_temp_c", sensor_range[0])),
        max_temp_c=int(payload.get("max_temp_c", sensor_range[1])),
    )


def _hard_upper_limit(task_spec: TaskSpec) -> int:
    success = dict(task_spec.payload.get("success", {}))
    thresholds = dict(success.get("thresholds", {}))
    return int(thresholds.get("hard_upper_limit_c", task_spec.target_band[1] + 4))


def _append_trace_sample(result: ScenarioResult, plant: ThermalChamberPlant) -> None:
    sample = TraceSample(
        timestamp_ms=plant.now_ms,
        values={
            "temperature_c": plant.temperature_c,
            "heater_on": plant.heater_on,
            "retained_heat_c": plant.retained_heat_c,
        },
    )
    if result.trace_samples and result.trace_samples[-1] == sample:
        return
    result.trace_samples.append(sample)


def _record_firmware_lines(
    client: UartTcpClient,
    transcript: Transcript,
    plant: ThermalChamberPlant,
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
        if line.startswith("ACT HEATER "):
            if line == "ACT HEATER ON":
                telemetry["saw_heater_on"] = True
            if line == "ACT HEATER OFF":
                telemetry["saw_heater_off"] = True
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


def _should_send_valid_frame(spec: ScenarioSpec, plant: ThermalChamberPlant) -> bool:
    if spec.name == "malformed_frame" and plant.now_ms > 0:
        return False
    if spec.send_valid_until_ms is None:
        return True
    return plant.now_ms <= spec.send_valid_until_ms


def _scenario_goal_reached(spec_name: str, telemetry: dict[str, object]) -> bool:
    if spec_name == "smoke":
        return bool(telemetry.get("saw_exchange", False))
    if spec_name == "sensor_timeout":
        return bool(telemetry.get("saw_heater_on", False) and telemetry.get("timeout_off_delta_ms") is not None)
    if spec_name == "malformed_frame":
        return bool(telemetry.get("safe_off_after_invalid", False))
    return False


def _settling_time_ms(samples: list[TraceSample], band_min: int, band_max: int) -> int | None:
    for index, sample in enumerate(samples):
        if all(band_min <= int(later.values["temperature_c"]) <= band_max for later in samples[index:]):
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
            "heater_transitions": None,
            "time_to_first_valid_actuation_ms": None,
            "constraint_violations": None,
            "no_progress_detected": True,
            "hard_limit_exceeded": True,
            "hard_limit_margin_c": None,
        }

    band_min, band_max = task_spec.target_band
    plant_min, plant_max = task_spec.primary_sensor_range or (15, 80)
    hard_upper_limit = _hard_upper_limit(task_spec)
    temperatures = [int(sample.values["temperature_c"]) for sample in samples]
    heater_states = [bool(sample.values.get("heater_on", False)) for sample in samples]
    transition_count = _count_transitions(samples, "heater_on")

    initial_heater_state = heater_states[0]
    first_actuation = next(
        (sample.timestamp_ms for sample in samples if bool(sample.values.get("heater_on", False)) != initial_heater_state),
        None,
    )
    rise_time_ms = next((sample.timestamp_ms for sample in samples if int(sample.values["temperature_c"]) >= band_min), None)
    settling_time_ms = _settling_time_ms(samples, band_min, band_max)
    constraint_violations = sum(1 for value in temperatures if value < plant_min or value > plant_max)
    max_temperature = max(temperatures)

    return {
        "sample_count": len(samples),
        "initial_temperature_c": temperatures[0],
        "final_temperature_c": temperatures[-1],
        "min_temperature_c": min(temperatures),
        "max_temperature_c": max_temperature,
        "steady_state_error": abs(temperatures[-1] - task_spec.target_band_center),
        "overshoot": max(0, max_temperature - band_max),
        "undershoot": max(0, band_min - min(temperatures)),
        "rise_time_ms": rise_time_ms,
        "settling_time_ms": settling_time_ms,
        "oscillation_detected": transition_count > 3,
        "heater_transitions": transition_count,
        "heater_full_scale_ratio": sum(1 for state in heater_states if state) / float(len(samples)),
        "time_to_first_valid_actuation_ms": first_actuation,
        "constraint_violations": constraint_violations,
        "no_progress_detected": len(set(temperatures)) <= 1,
        "duration_ms": samples[-1].timestamp_ms,
        "hard_limit_exceeded": max_temperature > hard_upper_limit,
        "hard_limit_margin_c": hard_upper_limit - max_temperature,
    }


def _evaluate_result(result: ScenarioResult, task_spec: TaskSpec) -> None:
    telemetry = result.telemetry
    metrics = _compute_trace_metrics(result.trace_samples, task_spec)
    timeout_min_ms, timeout_max_ms = task_spec.timeout_bounds_ms
    hard_upper_limit = _hard_upper_limit(task_spec)
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
    elif result.name == "warmup_control":
        checks.update(
            {
                "saw_heater_on": telemetry.get("saw_heater_on", False),
                "entered_target_band": telemetry.get("entered_target_band_ms") is not None,
                "hard_limit_respected": not metrics["hard_limit_exceeded"],
            }
        )
        if not checks["saw_heater_on"]:
            result.passed = False
            result.reason = "controller never turned the heater on"
        elif not checks["entered_target_band"]:
            result.passed = False
            result.reason = "chamber never reached the working band"
        elif not checks["hard_limit_respected"]:
            result.passed = False
            result.reason = f"temperature exceeded the hard upper limit of {hard_upper_limit} C"
        else:
            result.passed = True
            result.reason = "entered the working band without thermal runaway"
    elif result.name == "overshoot_guard":
        checks.update(
            {
                "saw_heater_on": telemetry.get("saw_heater_on", False),
                "saw_heater_off": telemetry.get("saw_heater_off", False),
                "hard_limit_respected": not metrics["hard_limit_exceeded"],
            }
        )
        if not checks["saw_heater_on"]:
            result.passed = False
            result.reason = "controller never turned the heater on"
        elif not checks["saw_heater_off"]:
            result.passed = False
            result.reason = "controller never turned the heater off near the upper band"
        elif not checks["hard_limit_respected"]:
            result.passed = False
            result.reason = f"temperature exceeded the hard upper limit of {hard_upper_limit} C"
        else:
            result.passed = True
            result.reason = "heater switched off early enough to contain thermal lag"
    elif result.name == "sensor_timeout":
        timeout_delta = telemetry.get("timeout_off_delta_ms")
        checks.update(
            {
                "saw_heater_on": telemetry.get("saw_heater_on", False),
                "timeout_off_detected": timeout_delta is not None,
                "timeout_off_delta_ms": timeout_delta,
            }
        )
        if not checks["saw_heater_on"]:
            result.passed = False
            result.reason = "controller never entered the heating state"
        elif timeout_delta is None:
            result.passed = False
            result.reason = "timeout-driven HEATER OFF was not observed"
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

    if metrics.get("hard_limit_exceeded"):
        observations.append(
            f"temperature peaked at {metrics['max_temperature_c']} C above the hard limit of {hard_upper_limit} C"
        )
    if (
        result.name in {"warmup_control", "overshoot_guard"}
        and telemetry.get("saw_heater_on", False)
        and int(metrics.get("max_temperature_c", 0) or 0) <= int(metrics.get("initial_temperature_c", 0) or 0)
    ):
        observations.append("heater-on commands were observed, but the chamber never warmed above its initial temperature")
    if result.name == "sensor_timeout" and telemetry.get("last_valid_send_ms") is not None and telemetry.get("timeout_off_delta_ms") is None:
        observations.append("valid sensor frames stopped, but no timeout-driven heater-off transition was observed")

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
    plant = ThermalChamberPlant(
        temperature_c=spec.initial_temperature_c,
        retained_heat_c=spec.initial_retained_heat_c,
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
            "saw_heater_on": False,
            "saw_heater_off": False,
            "entered_target_band_ms": None,
            "safe_off_after_invalid": False,
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
                    payload = "SENSE TEMP banana"
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
                if (
                    result.telemetry.get("entered_target_band_ms") is None
                    and task_spec.target_band[0] <= plant.temperature_c <= task_spec.target_band[1]
                ):
                    result.telemetry["entered_target_band_ms"] = plant.now_ms
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
