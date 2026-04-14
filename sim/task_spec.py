from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _expect_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _expect_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a JSON array")
    return value


def _expect_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _expect_int(value: Any, label: str) -> int:
    if not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _expect_signal_entries(value: Any, label: str) -> list[dict[str, Any]]:
    items = _expect_list(value, label)
    if not items:
        raise ValueError(f"{label} must not be empty")
    entries: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        entry = _expect_mapping(item, f"{label}[{index}]")
        _expect_string(entry.get("name"), f"{label}[{index}].name")
        _expect_string(entry.get("type"), f"{label}[{index}].type")
        if "units" in entry:
            _expect_string(entry.get("units"), f"{label}[{index}].units")
        if "safe_state" in entry:
            _expect_string(entry.get("safe_state"), f"{label}[{index}].safe_state")
        if "range" in entry:
            signal_range = _expect_list(entry.get("range"), f"{label}[{index}].range")
            if len(signal_range) != 2:
                raise ValueError(f"{label}[{index}].range must contain exactly two items")
        entries.append(entry)
    return entries


@dataclass(frozen=True)
class TaskSpec:
    source_path: Path
    payload: dict[str, Any]

    def validate(self) -> None:
        _expect_string(self.payload.get("experiment_id"), "experiment_id")
        _expect_string(self.payload.get("task_id"), "task_id")
        _expect_string(self.payload.get("task_name"), "task_name")
        _expect_string(self.payload.get("task_version"), "task_version")

        machine = _expect_mapping(self.payload.get("machine"), "machine")
        interface = _expect_mapping(machine.get("interface"), "machine.interface")
        _expect_string(interface.get("transport"), "machine.interface.transport")
        _expect_int(interface.get("baudrate"), "machine.interface.baudrate")
        if "notes" in machine:
            _expect_list(machine.get("notes"), "machine.notes")

        timing = _expect_mapping(self.payload.get("timing"), "timing")
        _expect_int(timing.get("control_period_ms"), "timing.control_period_ms")
        _expect_int(timing.get("sensor_period_ms"), "timing.sensor_period_ms")
        _expect_int(timing.get("sensor_timeout_ms"), "timing.sensor_timeout_ms")
        if "notes" in timing:
            _expect_list(timing.get("notes"), "timing.notes")

        plant = _expect_mapping(self.payload.get("plant"), "plant")
        if "notes" in plant:
            _expect_list(plant.get("notes"), "plant.notes")

        _expect_signal_entries(self.payload.get("sensors"), "sensors")
        _expect_signal_entries(self.payload.get("actuators"), "actuators")

        task = _expect_mapping(self.payload.get("task"), "task")
        _expect_string(task.get("objective"), "task.objective")
        target_band = _expect_mapping(task.get("target_band"), "task.target_band")
        _expect_int(target_band.get("min"), "task.target_band.min")
        _expect_int(target_band.get("max"), "task.target_band.max")
        _expect_list(task.get("policy"), "task.policy")
        for key in ("interface", "decision_summary", "state_model"):
            if key in task:
                _expect_list(task.get(key), f"task.{key}")
        if "constraints" in self.payload:
            _expect_list(self.payload.get("constraints"), "constraints")

        success = _expect_mapping(self.payload.get("success"), "success")
        _expect_list(success.get("required_scenarios"), "success.required_scenarios")
        _expect_mapping(success.get("thresholds"), "success.thresholds")
        if "notes" in success:
            _expect_list(success.get("notes"), "success.notes")

        feedback = _expect_mapping(self.payload.get("feedback", {}), "feedback")
        if feedback:
            _expect_string(feedback.get("mode", "full"), "feedback.mode")

    @property
    def experiment_id(self) -> str:
        return str(self.payload["experiment_id"])

    @property
    def task_id(self) -> str:
        return str(self.payload["task_id"])

    @property
    def task_name(self) -> str:
        return str(self.payload["task_name"])

    @property
    def task_version(self) -> str:
        return str(self.payload["task_version"])

    @property
    def runtime_id(self) -> str:
        return str(self.payload.get("runtime_id", self.task_id))

    @property
    def editable_paths(self) -> list[str]:
        return [str(path) for path in self.payload.get("editable_paths", [])]

    @property
    def feedback_config(self) -> dict[str, Any]:
        return dict(_expect_mapping(self.payload.get("feedback", {}), "feedback"))

    @property
    def scenario_names(self) -> list[str]:
        success = _expect_mapping(self.payload["success"], "success")
        return [str(name) for name in _expect_list(success["required_scenarios"], "success.required_scenarios")]

    @property
    def sensors(self) -> list[dict[str, Any]]:
        return [dict(item) for item in _expect_signal_entries(self.payload.get("sensors"), "sensors")]

    @property
    def actuators(self) -> list[dict[str, Any]]:
        return [dict(item) for item in _expect_signal_entries(self.payload.get("actuators"), "actuators")]

    @property
    def primary_sensor(self) -> dict[str, Any]:
        return self.sensors[0]

    @property
    def primary_sensor_range(self) -> tuple[int, int] | None:
        signal_range = self.primary_sensor.get("range")
        if not isinstance(signal_range, list) or len(signal_range) != 2:
            return None
        return int(signal_range[0]), int(signal_range[1])

    @property
    def target_band(self) -> tuple[int, int]:
        task = _expect_mapping(self.payload["task"], "task")
        target_band = _expect_mapping(task["target_band"], "task.target_band")
        return int(target_band["min"]), int(target_band["max"])

    @property
    def target_band_center(self) -> float:
        low, high = self.target_band
        return (low + high) / 2.0

    @property
    def timeout_bounds_ms(self) -> tuple[int, int]:
        success = _expect_mapping(self.payload["success"], "success")
        thresholds = _expect_mapping(success["thresholds"], "success.thresholds")
        return (
            int(thresholds["timeout_reaction_ms_min"]),
            int(thresholds["timeout_reaction_ms_max"]),
        )

    def to_json(self) -> dict[str, Any]:
        return dict(self.payload)

    def public_contract_payload(self) -> dict[str, Any]:
        success = _expect_mapping(self.payload["success"], "success")
        public_success = {
            "thresholds": dict(_expect_mapping(success["thresholds"], "success.thresholds")),
        }
        if "notes" in success:
            public_success["notes"] = [str(item) for item in _expect_list(success.get("notes"), "success.notes")]

        public_payload: dict[str, Any] = {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "task_version": self.task_version,
            "machine": dict(_expect_mapping(self.payload["machine"], "machine")),
            "sensors": self.sensors,
            "actuators": self.actuators,
            "timing": dict(_expect_mapping(self.payload["timing"], "timing")),
            "plant": dict(_expect_mapping(self.payload["plant"], "plant")),
            "initial_state": dict(_expect_mapping(self.payload.get("initial_state", {}), "initial_state")),
            "task": dict(_expect_mapping(self.payload["task"], "task")),
            "constraints": [str(item) for item in self.payload.get("constraints", [])],
            "success": public_success,
            "editable_paths": self.editable_paths,
        }
        if not public_payload["initial_state"]:
            public_payload.pop("initial_state")
        return public_payload

    def _signal_summary(self, signal: dict[str, Any], *, kind: str) -> str:
        parts = [f"{signal['name'].upper()}"]
        signal_range = signal.get("range")
        units = str(signal.get("units", "")).strip()
        if isinstance(signal_range, list) and len(signal_range) == 2:
            range_text = f"{signal_range[0]}..{signal_range[1]}"
            if units:
                range_text += f" {units}"
            parts.append(f"in {range_text}")
        parts.append(f"({signal['type']} {kind})")
        safe_state = str(signal.get("safe_state", "")).strip()
        if safe_state:
            parts.append(f"safe state {safe_state}")
        return " ".join(parts)

    def render_agent_summary(self) -> str:
        machine = _expect_mapping(self.payload["machine"], "machine")
        interface = _expect_mapping(machine["interface"], "machine.interface")
        timing = _expect_mapping(self.payload["timing"], "timing")
        plant = _expect_mapping(self.payload["plant"], "plant")
        task = _expect_mapping(self.payload["task"], "task")
        success = _expect_mapping(self.payload["success"], "success")
        policy = [str(item) for item in _expect_list(task["policy"], "task.policy")]
        interface_notes = [str(item) for item in task.get("interface", [])]
        decision_summary = [str(item) for item in task.get("decision_summary", [])]
        state_model = [str(item) for item in task.get("state_model", [])]
        constraints = [str(item) for item in self.payload.get("constraints", [])]
        machine_notes = [str(item) for item in machine.get("notes", [])]
        plant_notes = [str(item) for item in plant.get("notes", [])]
        timing_notes = [str(item) for item in timing.get("notes", [])]
        success_notes = [str(item) for item in success.get("notes", [])]
        low, high = self.target_band
        sensor = self.primary_sensor
        sensor_units = str(sensor.get("units", "")).strip()
        target_band_text = f"{low}..{high}"
        if sensor_units:
            target_band_text += f" {sensor_units}"

        lines = [
            f"# Task: {self.task_name}",
            "",
            f"Version: {self.task_version}",
            "",
            "## Objective",
            str(task["objective"]),
            "",
            "## Machine",
            f"- Target: {machine['controller']}",
            f"- Transport: {interface['transport']} on {interface['port']}",
            f"- Baud rate: {interface['baudrate']}",
            f"- Protocol: {interface['protocol']}",
        ]
        lines.extend(f"- {item}" for item in machine_notes)
        lines.extend(
            [
                "",
                "## Plant",
            ]
        )
        lines.extend(f"- Sensor: {self._signal_summary(signal, kind='sensor')}" for signal in self.sensors)
        lines.extend(f"- Actuator: {self._signal_summary(signal, kind='actuator')}" for signal in self.actuators)
        lines.extend(f"- {item}" for item in plant_notes)
        lines.extend(
            [
                "",
                "## Timing",
                f"- Controller step period: {timing['control_period_ms']} ms",
                f"- Sensor frame period: {timing['sensor_period_ms']} ms",
                f"- Sensor timeout: {timing['sensor_timeout_ms']} ms",
                "- The controller can be stepped between valid sensor frames during normal execution.",
                "- Treat idle/no-new-frame inputs differently from malformed input and true timeout conditions.",
            ]
        )
        lines.extend(f"- {item}" for item in timing_notes)
        if interface_notes:
            lines.extend(["", "## Interface"])
            lines.extend(f"- {item}" for item in interface_notes)
        lines.extend(["", "## Control Policy"])
        lines.extend(f"- {item}" for item in policy)
        if decision_summary:
            lines.extend(["", "## Decision Summary"])
            lines.extend(f"- {item}" for item in decision_summary)
        if state_model:
            lines.extend(["", "## State Model"])
            lines.extend(f"- {item}" for item in state_model)
        lines.extend(
            [
                "",
                "## Success",
                f"- Required scenarios: {', '.join(self.scenario_names)}",
                f"- Target band: {sensor['name'].upper()} {target_band_text}",
                f"- Timeout reaction bound: {self.timeout_bounds_ms[0]}..{self.timeout_bounds_ms[1]} ms",
            ]
        )
        lines.extend(f"- {item}" for item in success_notes)
        if constraints:
            lines.extend(["", "## Constraints"])
            lines.extend(f"- {item}" for item in constraints)
        return "\n".join(lines) + "\n"


def load_task_spec(path: Path | str) -> TaskSpec:
    source_path = Path(path).resolve()
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    spec = TaskSpec(source_path=source_path, payload=_expect_mapping(payload, "task spec"))
    spec.validate()
    return spec
