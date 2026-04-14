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
    initial_temp_c: int
    initial_level: int
    max_steps: int
    send_valid_until_ms: int | None = None
    invalid_at_ms: int | None = None
    invalid_frame: str | None = None


@dataclass(frozen=True)
class MixingTankPlantConfig:
    tick_ms: int = 100
    inlet_fill_delta: int = 7
    passive_drain_delta: int = 1
    ambient_temp_c: int = 24
    heater_gain_c: int = 3
    passive_cooling_c: int = 1
    retained_heat_gain_c: int = 2
    retained_heat_decay_c: int = 1
    max_retained_heat_c: int = 4
    min_temp_c: int = 20
    max_temp_c: int = 80
    min_level: int = 0
    max_level: int = 100
    min_heating_level: int = 55


@dataclass
class MixingTankPlant:
    temp_c: int
    level: int
    inlet_open: bool = False
    heater_on: bool = False
    retained_heat_c: int = 0
    now_ms: int = 0
    config: MixingTankPlantConfig = field(default_factory=MixingTankPlantConfig)

    def sense_temp_frame(self) -> str:
        return f"SENSE TEMP {self.temp_c}"

    def sense_level_frame(self) -> str:
        return f"SENSE LEVEL {self.level}"

    def apply_firmware_line(self, line: str) -> bool:
        normalized = line.strip()
        if normalized == "ACT INLET OPEN":
            self.inlet_open = True
            return True
        if normalized == "ACT INLET CLOSED":
            self.inlet_open = False
            return True
        if normalized == "ACT HEATER ON":
            self.heater_on = True
            return True
        if normalized == "ACT HEATER OFF":
            self.heater_on = False
            return True
        return False

    def step(self) -> tuple[int, int]:
        if self.inlet_open:
            self.level = min(self.config.max_level, self.level + self.config.inlet_fill_delta)
        else:
            self.level = max(self.config.min_level, self.level - self.config.passive_drain_delta)

        if self.heater_on and self.level >= self.config.min_heating_level:
            self.retained_heat_c = min(
                self.config.max_retained_heat_c,
                self.retained_heat_c + self.config.retained_heat_gain_c,
            )
        else:
            self.retained_heat_c = max(0, self.retained_heat_c - self.config.retained_heat_decay_c)

        delta = self.retained_heat_c // 2
        if self.heater_on and self.level >= self.config.min_heating_level:
            delta += self.config.heater_gain_c
        if self.temp_c > self.config.ambient_temp_c:
            delta -= self.config.passive_cooling_c

        self.temp_c = max(self.config.min_temp_c, min(self.config.max_temp_c, self.temp_c + delta))
        self.now_ms += self.config.tick_ms
        return self.temp_c, self.level


def available_runtime(repo_root: Path) -> tuple[bool, str]:
    return shared_available_runtime(repo_root)


def scenario_specs(task_spec: TaskSpec | None = None) -> dict[str, ScenarioSpec]:
    return {
        "smoke": ScenarioSpec(name="smoke", initial_temp_c=25, initial_level=35, max_steps=8, send_valid_until_ms=0),
        "fill_then_heat": ScenarioSpec(name="fill_then_heat", initial_temp_c=25, initial_level=35, max_steps=32),
        "low_level_guard": ScenarioSpec(name="low_level_guard", initial_temp_c=34, initial_level=50, max_steps=18),
        "anticipation_control": ScenarioSpec(name="anticipation_control", initial_temp_c=42, initial_level=66, max_steps=18),
        "sensor_timeout": ScenarioSpec(
            name="sensor_timeout",
            initial_temp_c=42,
            initial_level=66,
            max_steps=18,
            send_valid_until_ms=300,
        ),
        "malformed_frame": ScenarioSpec(
            name="malformed_frame",
            initial_temp_c=44,
            initial_level=65,
            max_steps=10,
            send_valid_until_ms=0,
            invalid_at_ms=100,
            invalid_frame="SENSE TEMP banana",
        ),
    }


def _plant_config(task_spec: TaskSpec) -> MixingTankPlantConfig:
    payload = dict(task_spec.payload.get("plant", {}))
    temp_range = task_spec.primary_sensor_range or (20, 80)
    return MixingTankPlantConfig(
        tick_ms=int(payload.get("tick_ms", 100)),
        inlet_fill_delta=int(payload.get("inlet_fill_delta", 7)),
        passive_drain_delta=int(payload.get("passive_drain_delta", 1)),
        ambient_temp_c=int(payload.get("ambient_temp_c", 24)),
        heater_gain_c=int(payload.get("heater_gain_c", 3)),
        passive_cooling_c=int(payload.get("passive_cooling_c", 1)),
        retained_heat_gain_c=int(payload.get("retained_heat_gain_c", 2)),
        retained_heat_decay_c=int(payload.get("retained_heat_decay_c", 1)),
        max_retained_heat_c=int(payload.get("max_retained_heat_c", 4)),
        min_temp_c=int(payload.get("min_temp_c", temp_range[0])),
        max_temp_c=int(payload.get("max_temp_c", temp_range[1])),
        min_level=int(payload.get("min_level", 0)),
        max_level=int(payload.get("max_level", 100)),
        min_heating_level=int(payload.get("min_heating_level", 55)),
    )


def _hard_upper_limit(task_spec: TaskSpec) -> int:
    success = dict(task_spec.payload.get("success", {}))
    thresholds = dict(success.get("thresholds", {}))
    return int(thresholds.get("hard_upper_limit_c", task_spec.target_band[1] + 3))


def _append_trace_sample(result: ScenarioResult, plant: MixingTankPlant) -> None:
    sample = TraceSample(
        timestamp_ms=plant.now_ms,
        values={
            "temp_c": plant.temp_c,
            "level": plant.level,
            "inlet_open": plant.inlet_open,
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
    plant: MixingTankPlant,
    result: ScenarioResult,
    task_spec: TaskSpec,
    last_valid_send_monotonic: float | None,
) -> None:
    telemetry = result.telemetry
    actuator_lines: list[str] = []

    for line in client.read_pending_lines():
        transcript.record(plant.now_ms / 1000.0, "fw->plant", line)
        if line == "DBG BOOTED":
            telemetry["saw_boot"] = True
            telemetry["firmware_ready"] = True
        if "main_task: Calling app_main()" in line or "main_task: Returned from app_main()" in line:
            telemetry["firmware_ready"] = True
        if line.startswith("ACT INLET ") or line.startswith("ACT HEATER "):
            actuator_lines.append(line)
            if line == "ACT INLET OPEN":
                telemetry["saw_inlet_open"] = True
            elif line == "ACT INLET CLOSED":
                telemetry["saw_inlet_closed"] = True
            elif line == "ACT HEATER ON":
                telemetry["saw_heater_on"] = True
            elif line == "ACT HEATER OFF":
                telemetry["saw_heater_off"] = True
                if task_spec.target_band[0] <= plant.temp_c <= task_spec.target_band[1]:
                    telemetry["early_heater_off"] = True

    if not actuator_lines:
        return

    for line in actuator_lines:
        plant.apply_firmware_line(line)

    if telemetry.get("last_valid_send_ms") is not None or telemetry.get("invalid_send_ms") is not None:
        telemetry["saw_exchange"] = True

    if plant.heater_on and plant.level < plant.config.min_heating_level:
        telemetry["low_level_heating_violations"] = int(telemetry.get("low_level_heating_violations", 0)) + 1

    if (
        telemetry.get("invalid_send_ms") is not None
        and plant.now_ms >= int(telemetry["invalid_send_ms"])
        and (not plant.heater_on)
        and (not plant.inlet_open)
    ):
        telemetry["safe_after_invalid"] = True

    if last_valid_send_monotonic is not None and telemetry.get("timeout_safe_delta_ms") is None:
        elapsed_ms = int(round((time.monotonic() - last_valid_send_monotonic) * 1000.0))
        if elapsed_ms >= task_spec.timeout_bounds_ms[0] and (not plant.heater_on) and (not plant.inlet_open):
            telemetry["timeout_safe_ms"] = plant.now_ms
            telemetry["timeout_safe_delta_ms"] = elapsed_ms

    _append_trace_sample(result, plant)


def _should_send_valid_frame(spec: ScenarioSpec, plant: MixingTankPlant) -> bool:
    if spec.name == "malformed_frame" and plant.now_ms > 0:
        return False
    if spec.send_valid_until_ms is None:
        return True
    return plant.now_ms <= spec.send_valid_until_ms


def _scenario_goal_reached(spec_name: str, telemetry: dict[str, object]) -> bool:
    if spec_name == "smoke":
        return bool(telemetry.get("saw_exchange", False))
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
            "final_temp_c": None,
            "final_level": None,
            "max_temp_c": None,
            "min_temp_c": None,
            "entered_target_band_ms": None,
            "overshoot": None,
            "hard_limit_exceeded": True,
            "hard_limit_margin_c": None,
            "heater_transitions": None,
            "inlet_transitions": None,
            "low_level_heating_violations": None,
            "constraint_violations": None,
            "duration_ms": None,
            "no_progress_detected": True,
        }

    hard_upper_limit = _hard_upper_limit(task_spec)
    temps = [int(sample.values["temp_c"]) for sample in samples]
    levels = [int(sample.values["level"]) for sample in samples]
    max_temp = max(temps)
    min_temp = min(temps)
    entered_target_band_ms = next(
        (sample.timestamp_ms for sample in samples if task_spec.target_band[0] <= int(sample.values["temp_c"]) <= task_spec.target_band[1]),
        None,
    )
    return {
        "sample_count": len(samples),
        "final_temp_c": temps[-1],
        "final_level": levels[-1],
        "max_temp_c": max_temp,
        "min_temp_c": min_temp,
        "entered_target_band_ms": entered_target_band_ms,
        "overshoot": max(0, max_temp - task_spec.target_band[1]),
        "hard_limit_exceeded": max_temp > hard_upper_limit,
        "hard_limit_margin_c": hard_upper_limit - max_temp,
        "heater_transitions": _count_transitions(samples, "heater_on"),
        "inlet_transitions": _count_transitions(samples, "inlet_open"),
        "low_level_heating_violations": sum(
            1 for sample in samples if bool(sample.values.get("heater_on", False)) and int(sample.values["level"]) < 55
        ),
        "constraint_violations": sum(1 for level in levels if level < 0 or level > 100),
        "duration_ms": samples[-1].timestamp_ms,
        "no_progress_detected": len(set(temps)) <= 1,
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
        "hard_limit_respected": not metrics["hard_limit_exceeded"],
        "low_level_heating_respected": int(metrics.get("low_level_heating_violations", 0) or 0) == 0,
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
    elif result.name == "fill_then_heat":
        checks["saw_inlet_open"] = telemetry.get("saw_inlet_open", False)
        checks["saw_heater_on"] = telemetry.get("saw_heater_on", False)
        checks["entered_target_band"] = metrics.get("entered_target_band_ms") is not None
        if not checks["saw_inlet_open"]:
            result.passed = False
            result.reason = "controller never opened the inlet"
        elif not checks["saw_heater_on"]:
            result.passed = False
            result.reason = "controller never entered the heating state"
        elif not checks["entered_target_band"]:
            result.passed = False
            result.reason = "temperature never reached the working band"
        elif not checks["low_level_heating_respected"]:
            result.passed = False
            result.reason = "heater was active below the minimum heating level"
        elif not checks["hard_limit_respected"]:
            result.passed = False
            result.reason = f"temperature exceeded the hard upper limit of {hard_upper_limit} C"
        else:
            result.passed = True
            result.reason = "filled safely and heated into the working band"
    elif result.name == "low_level_guard":
        checks["saw_inlet_open"] = telemetry.get("saw_inlet_open", False)
        if not checks["saw_inlet_open"]:
            result.passed = False
            result.reason = "controller never reopened the inlet at low level"
        elif not checks["low_level_heating_respected"]:
            result.passed = False
            result.reason = "heater was active while the vessel level was too low"
        else:
            result.passed = True
            result.reason = "heater stayed off until level was safe"
    elif result.name == "anticipation_control":
        checks["saw_heater_on"] = telemetry.get("saw_heater_on", False)
        checks["early_heater_off"] = telemetry.get("early_heater_off", False)
        if not checks["saw_heater_on"]:
            result.passed = False
            result.reason = "controller never turned the heater on"
        elif not checks["early_heater_off"]:
            result.passed = False
            result.reason = "controller never switched the heater off early near the upper band"
        elif not checks["hard_limit_respected"]:
            result.passed = False
            result.reason = f"temperature exceeded the hard upper limit of {hard_upper_limit} C"
        else:
            result.passed = True
            result.reason = "heater switched off early enough to contain thermal lag"
    elif result.name == "sensor_timeout":
        timeout_delta = telemetry.get("timeout_safe_delta_ms")
        checks["saw_heater_on"] = telemetry.get("saw_heater_on", False)
        checks["timeout_safe_delta_ms"] = timeout_delta
        if not checks["saw_heater_on"]:
            result.passed = False
            result.reason = "controller never entered the heating state before sensor loss"
        elif timeout_delta is None:
            result.passed = False
            result.reason = "timeout-driven safe shutdown was not observed"
        elif int(timeout_delta) < timeout_min_ms or int(timeout_delta) > timeout_max_ms:
            result.passed = False
            result.reason = f"timeout reaction bound violated: {timeout_delta} ms"
        else:
            result.passed = True
            result.reason = "sensor timeout forced a bounded safe shutdown"
    elif result.name == "malformed_frame":
        checks["safe_after_invalid"] = telemetry.get("safe_after_invalid", False)
        result.passed = bool(checks["safe_after_invalid"])
        result.reason = (
            "malformed input triggered the safe all-off state"
            if result.passed
            else "malformed input did not trigger the safe all-off state"
        )
    else:
        result.passed = False
        result.reason = f"unknown scenario {result.name}"

    if metrics.get("hard_limit_exceeded"):
        observations.append(f"temperature peaked at {metrics['max_temp_c']} C above the hard limit of {hard_upper_limit} C")
    if not checks["low_level_heating_respected"]:
        observations.append("heater was observed on while level was below the minimum heating threshold")
    if metrics.get("no_progress_detected"):
        observations.append("temperature never moved away from its initial value")
    if result.name == "sensor_timeout" and telemetry.get("last_valid_send_ms") is not None and telemetry.get("timeout_safe_delta_ms") is None:
        observations.append("sensor frames stopped, but the controller did not return to the safe all-off state in time")

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
    plant = MixingTankPlant(
        temp_c=spec.initial_temp_c,
        level=spec.initial_level,
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
            "saw_inlet_open": False,
            "saw_inlet_closed": False,
            "saw_heater_on": False,
            "saw_heater_off": False,
            "entered_target_band_ms": None,
            "early_heater_off": False,
            "low_level_heating_violations": 0,
            "timeout_safe_ms": None,
            "timeout_safe_delta_ms": None,
            "safe_after_invalid": False,
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
                    for payload in (plant.sense_temp_frame(), plant.sense_level_frame()):
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
                    and task_spec.target_band[0] <= plant.temp_c <= task_spec.target_band[1]
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
