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
    initial_turbidity_ntu: int
    initial_level: int
    max_steps: int
    send_valid_until_ms: int | None = None
    invalid_at_ms: int | None = None
    invalid_frame: str | None = None
    disturbance_events: dict[int, int] = field(default_factory=dict)


@dataclass(frozen=True)
class FilterTankPlantConfig:
    tick_ms: int = 100
    filter_improvement_ntu: int = 14
    rebound_ntu: int = 4
    drain_delta: int = 12
    min_turbidity_ntu: int = 0
    max_turbidity_ntu: int = 100
    min_level: int = 0
    max_level: int = 100


@dataclass
class FilterTankPlant:
    turbidity_ntu: int
    level: int
    filter_on: bool = False
    drain_open: bool = False
    now_ms: int = 0
    config: FilterTankPlantConfig = field(default_factory=FilterTankPlantConfig)

    def sense_turbidity_frame(self) -> str:
        return f"SENSE TURB {self.turbidity_ntu}"

    def sense_level_frame(self) -> str:
        return f"SENSE LEVEL {self.level}"

    def apply_firmware_line(self, line: str) -> bool:
        normalized = line.strip()
        if normalized == "ACT FILTER ON":
            self.filter_on = True
            return True
        if normalized == "ACT FILTER OFF":
            self.filter_on = False
            return True
        if normalized == "ACT DRAIN OPEN":
            self.drain_open = True
            return True
        if normalized == "ACT DRAIN CLOSED":
            self.drain_open = False
            return True
        return False

    def step(self) -> tuple[int, int]:
        if self.filter_on:
            self.turbidity_ntu = max(
                self.config.min_turbidity_ntu,
                self.turbidity_ntu - self.config.filter_improvement_ntu,
            )
        else:
            self.turbidity_ntu = min(
                self.config.max_turbidity_ntu,
                self.turbidity_ntu + self.config.rebound_ntu,
            )

        if self.drain_open:
            self.level = max(self.config.min_level, self.level - self.config.drain_delta)

        self.now_ms += self.config.tick_ms
        return self.turbidity_ntu, self.level


def available_runtime(repo_root: Path) -> tuple[bool, str]:
    return shared_available_runtime(repo_root)


def scenario_specs(task_spec: TaskSpec | None = None) -> dict[str, ScenarioSpec]:
    return {
        "smoke": ScenarioSpec(name="smoke", initial_turbidity_ntu=82, initial_level=72, max_steps=8, send_valid_until_ms=0),
        "clarification_cycle": ScenarioSpec(name="clarification_cycle", initial_turbidity_ntu=82, initial_level=72, max_steps=28),
        "settling_reset": ScenarioSpec(
            name="settling_reset",
            initial_turbidity_ntu=52,
            initial_level=72,
            max_steps=32,
            disturbance_events={600: 48},
        ),
        "disturbance_recovery": ScenarioSpec(
            name="disturbance_recovery",
            initial_turbidity_ntu=60,
            initial_level=72,
            max_steps=36,
            disturbance_events={800: 58},
        ),
        "sensor_timeout": ScenarioSpec(
            name="sensor_timeout",
            initial_turbidity_ntu=60,
            initial_level=72,
            max_steps=18,
            send_valid_until_ms=300,
        ),
        "malformed_frame": ScenarioSpec(
            name="malformed_frame",
            initial_turbidity_ntu=50,
            initial_level=72,
            max_steps=10,
            send_valid_until_ms=0,
            invalid_at_ms=100,
            invalid_frame="SENSE TURB banana",
        ),
    }


def _plant_config(task_spec: TaskSpec) -> FilterTankPlantConfig:
    payload = dict(task_spec.payload.get("plant", {}))
    sensor_range = task_spec.primary_sensor_range or (0, 100)
    return FilterTankPlantConfig(
        tick_ms=int(payload.get("tick_ms", 100)),
        filter_improvement_ntu=int(payload.get("filter_improvement_ntu", 14)),
        rebound_ntu=int(payload.get("rebound_ntu", 4)),
        drain_delta=int(payload.get("drain_delta", 12)),
        min_turbidity_ntu=int(payload.get("min_turbidity_ntu", sensor_range[0])),
        max_turbidity_ntu=int(payload.get("max_turbidity_ntu", sensor_range[1])),
        min_level=int(payload.get("min_level", 0)),
        max_level=int(payload.get("max_level", 100)),
    )


def _settling_window_ms(task_spec: TaskSpec) -> int:
    success = dict(task_spec.payload.get("success", {}))
    thresholds = dict(success.get("thresholds", {}))
    return int(thresholds.get("settling_window_ms", 400))


def _append_trace_sample(result: ScenarioResult, plant: FilterTankPlant) -> None:
    sample = TraceSample(
        timestamp_ms=plant.now_ms,
        values={
            "turbidity_ntu": plant.turbidity_ntu,
            "level": plant.level,
            "filter_on": plant.filter_on,
            "drain_open": plant.drain_open,
        },
    )
    if result.trace_samples and result.trace_samples[-1] == sample:
        return
    result.trace_samples.append(sample)


def _record_firmware_lines(
    client: UartTcpClient,
    transcript: Transcript,
    plant: FilterTankPlant,
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
        if line.startswith("ACT FILTER ") or line.startswith("ACT DRAIN "):
            actuator_lines.append(line)
            if line == "ACT FILTER ON":
                telemetry["saw_filter_on"] = True
            elif line == "ACT FILTER OFF":
                telemetry["saw_filter_off"] = True
            elif line == "ACT DRAIN OPEN":
                telemetry["saw_drain_open"] = True
            elif line == "ACT DRAIN CLOSED":
                telemetry["saw_drain_closed"] = True

    if not actuator_lines:
        return

    previous_filter_on = plant.filter_on
    previous_drain_open = plant.drain_open
    for line in actuator_lines:
        plant.apply_firmware_line(line)

    if telemetry.get("last_valid_send_ms") is not None or telemetry.get("invalid_send_ms") is not None:
        telemetry["saw_exchange"] = True

    if telemetry.get("saw_filter_on", False) and previous_filter_on and (not plant.filter_on) and (not plant.drain_open):
        if telemetry.get("entered_settling_ms") is None:
            telemetry["entered_settling_ms"] = plant.now_ms
            telemetry["entered_settling_monotonic"] = time.monotonic()

    if (not previous_drain_open) and plant.drain_open and telemetry.get("entered_draining_ms") is None:
        telemetry["entered_draining_ms"] = plant.now_ms

    settling_start = telemetry.get("entered_settling_ms")
    settling_start_monotonic = telemetry.get("entered_settling_monotonic")
    if plant.drain_open:
        settling_elapsed_ms = None
        if isinstance(settling_start_monotonic, (int, float)):
            settling_elapsed_ms = int(round((time.monotonic() - float(settling_start_monotonic)) * 1000.0))
        if (
            settling_start is None or
            settling_elapsed_ms is None or
            settling_elapsed_ms < _settling_window_ms(task_spec) or
            plant.turbidity_ntu > task_spec.target_band[1]
        ):
            telemetry["early_drain_violations"] = int(telemetry.get("early_drain_violations", 0)) + 1

    if (
        telemetry.get("settling_disturbance_ms") is not None
        and plant.filter_on
        and (not plant.drain_open)
        and plant.now_ms >= int(telemetry["settling_disturbance_ms"])
    ):
        telemetry["settling_reset_observed"] = True

    if (
        telemetry.get("draining_disturbance_ms") is not None
        and plant.filter_on
        and (not plant.drain_open)
        and plant.now_ms >= int(telemetry["draining_disturbance_ms"])
    ):
        telemetry["disturbance_recovery_observed"] = True

    if (
        telemetry.get("invalid_send_ms") is not None
        and plant.now_ms >= int(telemetry["invalid_send_ms"])
        and (not plant.filter_on)
        and (not plant.drain_open)
    ):
        telemetry["safe_after_invalid"] = True

    if last_valid_send_monotonic is not None and telemetry.get("timeout_safe_delta_ms") is None:
        elapsed_ms = int(round((time.monotonic() - last_valid_send_monotonic) * 1000.0))
        if elapsed_ms >= task_spec.timeout_bounds_ms[0] and (not plant.filter_on) and (not plant.drain_open):
            telemetry["timeout_safe_ms"] = plant.now_ms
            telemetry["timeout_safe_delta_ms"] = elapsed_ms

    _append_trace_sample(result, plant)


def _should_send_valid_frame(spec: ScenarioSpec, plant: FilterTankPlant) -> bool:
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


def _compute_trace_metrics(samples: list[TraceSample], task_spec: TaskSpec, result: ScenarioResult) -> dict[str, object]:
    if not samples:
        return {
            "sample_count": 0,
            "final_turbidity_ntu": None,
            "final_level": None,
            "clear_band_reached_ms": None,
            "drain_open_while_cloudy_samples": None,
            "filter_transitions": None,
            "drain_transitions": None,
            "constraint_violations": None,
            "early_drain_violations": None,
            "duration_ms": None,
            "no_progress_detected": True,
        }

    turbidity_values = [int(sample.values["turbidity_ntu"]) for sample in samples]
    levels = [int(sample.values["level"]) for sample in samples]
    clear_band_reached_ms = next(
        (sample.timestamp_ms for sample in samples if int(sample.values["turbidity_ntu"]) <= task_spec.target_band[1]),
        None,
    )
    return {
        "sample_count": len(samples),
        "final_turbidity_ntu": turbidity_values[-1],
        "final_level": levels[-1],
        "clear_band_reached_ms": clear_band_reached_ms,
        "drain_open_while_cloudy_samples": sum(
            1
            for sample in samples
            if bool(sample.values.get("drain_open", False)) and int(sample.values["turbidity_ntu"]) > task_spec.target_band[1]
        ),
        "filter_transitions": _count_transitions(samples, "filter_on"),
        "drain_transitions": _count_transitions(samples, "drain_open"),
        "constraint_violations": sum(
            1 for value in turbidity_values if value < 0 or value > 100
        ) + sum(1 for level in levels if level < 0 or level > 100),
        "early_drain_violations": int(result.telemetry.get("early_drain_violations", 0) or 0),
        "duration_ms": samples[-1].timestamp_ms,
        "no_progress_detected": len(set(turbidity_values)) <= 1 and len(set(levels)) <= 1,
    }


def _evaluate_result(result: ScenarioResult, task_spec: TaskSpec) -> None:
    telemetry = result.telemetry
    metrics = _compute_trace_metrics(result.trace_samples, task_spec, result)
    timeout_min_ms, timeout_max_ms = task_spec.timeout_bounds_ms
    checks: dict[str, object] = {
        "firmware_ready": telemetry.get("firmware_ready", False),
        "saw_exchange": telemetry.get("saw_exchange", False),
        "runtime_timeout": telemetry.get("runtime_timeout", False),
        "no_early_drain": int(metrics.get("early_drain_violations", 0) or 0) == 0,
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
    elif result.name == "clarification_cycle":
        checks["saw_filter_on"] = telemetry.get("saw_filter_on", False)
        checks["entered_settling"] = telemetry.get("entered_settling_ms") is not None
        checks["entered_draining"] = telemetry.get("entered_draining_ms") is not None
        checks["completed"] = telemetry.get("complete_ms") is not None
        if not checks["saw_filter_on"]:
            result.passed = False
            result.reason = "controller never turned the filter on"
        elif not checks["entered_settling"]:
            result.passed = False
            result.reason = "controller never entered the settling state"
        elif not checks["entered_draining"]:
            result.passed = False
            result.reason = "controller never opened the drain after settling"
        elif not checks["completed"]:
            result.passed = False
            result.reason = "controller never completed the cycle"
        elif not checks["no_early_drain"]:
            result.passed = False
            result.reason = "drain opened before the clear-and-settle conditions were satisfied"
        else:
            result.passed = True
            result.reason = "completed the filter-settle-drain cycle"
    elif result.name == "settling_reset":
        checks["settling_reset_observed"] = telemetry.get("settling_reset_observed", False)
        checks["completed"] = telemetry.get("complete_ms") is not None
        if not checks["settling_reset_observed"]:
            result.passed = False
            result.reason = "settling disturbance did not drive the controller back to filtering"
        elif not checks["completed"]:
            result.passed = False
            result.reason = "controller did not recover and complete the cycle after the settling disturbance"
        elif not checks["no_early_drain"]:
            result.passed = False
            result.reason = "drain opened before the clear-and-settle conditions were satisfied"
        else:
            result.passed = True
            result.reason = "settling disturbance correctly reset the cycle"
    elif result.name == "disturbance_recovery":
        checks["disturbance_recovery_observed"] = telemetry.get("disturbance_recovery_observed", False)
        checks["completed"] = telemetry.get("complete_ms") is not None
        if not checks["disturbance_recovery_observed"]:
            result.passed = False
            result.reason = "draining disturbance did not drive the controller back to filtering"
        elif not checks["completed"]:
            result.passed = False
            result.reason = "controller did not recover and complete the cycle after the draining disturbance"
        elif not checks["no_early_drain"]:
            result.passed = False
            result.reason = "drain opened before the clear-and-settle conditions were satisfied"
        else:
            result.passed = True
            result.reason = "draining disturbance correctly restarted filtration"
    elif result.name == "sensor_timeout":
        timeout_delta = telemetry.get("timeout_safe_delta_ms")
        checks["saw_filter_on"] = telemetry.get("saw_filter_on", False)
        checks["timeout_safe_delta_ms"] = timeout_delta
        if not checks["saw_filter_on"]:
            result.passed = False
            result.reason = "controller never entered the filtering state before sensor loss"
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

    if not checks["no_early_drain"]:
        observations.append("drain opened while the liquid was still cloudy or before settling completed")
    if metrics.get("no_progress_detected"):
        observations.append("the plant never moved away from its initial turbidity/level state")
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
    plant = FilterTankPlant(
        turbidity_ntu=spec.initial_turbidity_ntu,
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
            "saw_filter_on": False,
            "saw_filter_off": False,
            "saw_drain_open": False,
            "saw_drain_closed": False,
            "entered_settling_ms": None,
            "entered_settling_monotonic": None,
            "entered_draining_ms": None,
            "complete_ms": None,
            "settling_disturbance_ms": None,
            "draining_disturbance_ms": None,
            "settling_reset_observed": False,
            "disturbance_recovery_observed": False,
            "timeout_safe_ms": None,
            "timeout_safe_delta_ms": None,
            "safe_after_invalid": False,
            "early_drain_violations": 0,
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

                if plant.now_ms in spec.disturbance_events:
                    plant.turbidity_ntu = max(0, min(100, spec.disturbance_events[plant.now_ms]))
                    if result.telemetry.get("entered_draining_ms") is not None:
                        result.telemetry["draining_disturbance_ms"] = plant.now_ms
                    elif result.telemetry.get("entered_settling_ms") is not None:
                        result.telemetry["settling_disturbance_ms"] = plant.now_ms

                if _should_send_valid_frame(spec, plant):
                    for payload in (plant.sense_turbidity_frame(), plant.sense_level_frame()):
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
                if plant.level < 15 and (not plant.drain_open) and result.telemetry.get("complete_ms") is None:
                    result.telemetry["complete_ms"] = plant.now_ms
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
