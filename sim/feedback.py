from __future__ import annotations

import json
import re
from typing import Any


MODE_DEFAULTS = {
    "minimal": {
        "include_error_details": False,
        "include_build_logs": False,
        "include_runtime_logs": False,
        "include_test_logs": False,
        "include_uart_transcript": False,
        "include_trace_samples": False,
        "include_metrics": False,
        "include_failure_category": False,
        "include_history": False,
        "include_unit_test_details": False,
        "include_warnings": False,
        "include_evaluator_commentary": False,
    },
    "errors_only": {
        "include_error_details": True,
        "include_build_logs": False,
        "include_runtime_logs": False,
        "include_test_logs": False,
        "include_uart_transcript": False,
        "include_trace_samples": False,
        "include_metrics": False,
        "include_failure_category": True,
        "include_history": False,
        "include_unit_test_details": True,
        "include_warnings": False,
        "include_evaluator_commentary": True,
    },
    "metrics_only": {
        "include_error_details": False,
        "include_build_logs": False,
        "include_runtime_logs": False,
        "include_test_logs": False,
        "include_uart_transcript": False,
        "include_trace_samples": False,
        "include_metrics": True,
        "include_failure_category": True,
        "include_history": False,
        "include_unit_test_details": True,
        "include_warnings": False,
        "include_evaluator_commentary": True,
    },
    "logs_only": {
        "include_error_details": True,
        "include_build_logs": True,
        "include_runtime_logs": True,
        "include_test_logs": True,
        "include_uart_transcript": True,
        "include_trace_samples": False,
        "include_metrics": False,
        "include_failure_category": True,
        "include_history": False,
        "include_unit_test_details": True,
        "include_warnings": True,
        "include_evaluator_commentary": True,
    },
    "traces_only": {
        "include_error_details": False,
        "include_build_logs": False,
        "include_runtime_logs": False,
        "include_test_logs": False,
        "include_uart_transcript": True,
        "include_trace_samples": True,
        "include_metrics": False,
        "include_failure_category": True,
        "include_history": False,
        "include_unit_test_details": True,
        "include_warnings": False,
        "include_evaluator_commentary": True,
    },
    "full": {
        "include_error_details": True,
        "include_build_logs": True,
        "include_runtime_logs": True,
        "include_test_logs": True,
        "include_uart_transcript": True,
        "include_trace_samples": True,
        "include_metrics": True,
        "include_failure_category": True,
        "include_history": False,
        "include_unit_test_details": True,
        "include_warnings": True,
        "include_evaluator_commentary": True,
    },
}


HIDDEN_PATH_PATTERNS = (
    (
        re.compile(r"/tmp/embedded_eval_hidden_harness/[^/\s]+/[^/\s]+/([^\s]+)"),
        r"hidden_harness:\1",
    ),
    (
        re.compile(r"/tmp/embedded_eval_hidden_runs/[^/\s]+/[^/\s]+/([^\s]+)"),
        r"hidden_runs:\1",
    ),
)

JSON_FRAGMENT_PATTERN = re.compile(r'^"[^"]+":')


def normalize_feedback_config(raw_config: dict[str, Any] | None) -> dict[str, Any]:
    config = dict(raw_config or {})
    mode = str(config.get("mode", "full"))
    if mode not in MODE_DEFAULTS:
        raise ValueError(f"unknown feedback mode: {mode}")
    merged = dict(MODE_DEFAULTS[mode])
    merged.update(config)
    merged["mode"] = mode
    return merged


def _stage_summary(stage: dict[str, Any]) -> dict[str, Any]:
    ran = bool(stage)
    return {
        "ran": ran,
        "success": stage.get("success", False) if ran else False,
        "return_code": stage.get("returncode") if ran else None,
        "duration_s": stage.get("duration_s") if ran else None,
    }


def _sanitize_text(value: str) -> str:
    sanitized = value
    for pattern, replacement in HIDDEN_PATH_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_value(item) for key, item in value.items()}
    return value


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _clean_stage_messages(
    messages: list[str] | None,
    *,
    stage_success: bool = False,
    hide_json_fragments: bool = False,
) -> list[str]:
    cleaned: list[str] = []
    for raw_message in messages or []:
        message = str(raw_message).strip()
        lower_message = message.lower()
        if not message:
            continue
        if stage_success:
            if "0 tests failed" in message:
                continue
            if not any(token in lower_message for token in ("warning", "warn", "error", "failed", "assertion")):
                continue
        if hide_json_fragments and JSON_FRAGMENT_PATTERN.match(message):
            continue
        cleaned.append(message)
    return _dedupe_preserve_order(cleaned)


def _failed_scenario_observations(scenario: dict[str, Any]) -> list[str]:
    metrics = scenario.get("metrics", {})
    observations = [str(item) for item in scenario.get("observations", [])]

    initial_level = metrics.get("initial_level")
    min_level = metrics.get("min_level")
    max_level = metrics.get("max_level")
    final_level = metrics.get("final_level")
    if None not in (initial_level, min_level, max_level, final_level):
        observations.append(f"level range {min_level}..{max_level} from initial {initial_level}; final level {final_level}")

    initial_temperature = metrics.get("initial_temperature_c")
    min_temperature = metrics.get("min_temperature_c")
    max_temperature = metrics.get("max_temperature_c")
    final_temperature = metrics.get("final_temperature_c")
    if None not in (initial_temperature, min_temperature, max_temperature, final_temperature):
        observations.append(
            f"temperature range {min_temperature}..{max_temperature} C from initial {initial_temperature} C; final temperature {final_temperature} C"
        )

    actuator_transitions = metrics.get("pump_transitions")
    if actuator_transitions is None:
        actuator_transitions = metrics.get("heater_transitions")
    sample_count = metrics.get("sample_count")
    if metrics.get("oscillation_detected"):
        detail_parts = []
        if actuator_transitions is not None:
            transition_label = "pump transitions" if metrics.get("pump_transitions") is not None else "heater transitions"
            detail_parts.append(f"{actuator_transitions} {transition_label}")
        if sample_count is not None:
            detail_parts.append(f"{sample_count} samples")
        if detail_parts:
            observations.append(f"oscillation detected ({', '.join(detail_parts)})")
        else:
            observations.append("oscillation detected")

    if scenario.get("name") == "happy_path" and scenario.get("saw_pump_on") and None not in (initial_level, max_level):
        if max_level <= initial_level:
            observations.append("pump-on commands were observed, but the tank never rose above its initial level")

    if scenario.get("name") in {"warmup_control", "overshoot_guard"} and scenario.get("saw_heater_on") and None not in (
        initial_temperature,
        max_temperature,
    ):
        if max_temperature <= initial_temperature:
            observations.append("heater-on commands were observed, but the chamber never warmed above its initial temperature")

    if scenario.get("name") == "sensor_timeout" and scenario.get("timeout_off_delta_ms") is None:
        last_valid_send_ms = scenario.get("last_valid_send_ms")
        if last_valid_send_ms is not None:
            observations.append(
                f"last valid sensor frame arrived at {last_valid_send_ms} ms and no timeout-driven OFF was observed"
            )
        else:
            observations.append("no timeout-driven OFF was observed after valid sensor input stopped")

    return _dedupe_preserve_order(observations)


def project_feedback(raw_feedback: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    feedback_config = normalize_feedback_config(config or raw_feedback.get("feedback_config"))
    stages = raw_feedback.get("stages", {})
    summary = dict(raw_feedback.get("summary", {}))
    build_stage = stages.get("build", {})
    flash_stage = stages.get("flash_image", {})
    run_stage = stages.get("qemu_smoke", {})
    host_stage = stages.get("host_tests", {})
    integration_stage = stages.get("integration", {})

    view: dict[str, Any] = {
        "feedback_mode": feedback_config["mode"],
        "task": raw_feedback.get("task", {}),
        "build": _stage_summary(build_stage),
        "upload": _stage_summary(flash_stage),
        "run": _stage_summary(run_stage),
        "tests": {
            "host_unit_tests": _stage_summary(host_stage),
            "integration": _stage_summary(integration_stage),
        },
        "summary": {
            "status": summary.get("status"),
            "task_solved": summary.get("task_solved", False),
        },
    }

    if feedback_config["include_failure_category"]:
        view["summary"]["failure_category"] = summary.get("failure_category")

    if feedback_config["include_evaluator_commentary"]:
        view["summary"]["commentary"] = summary.get("commentary")

    if feedback_config["include_unit_test_details"]:
        view["tests"]["host_unit_tests"].update(
            {
                "errors": _clean_stage_messages(host_stage.get("errors", []), stage_success=bool(host_stage.get("success", False))),
                "warnings": _clean_stage_messages(host_stage.get("warnings", [])),
            }
        )

    if feedback_config["include_test_logs"]:
        view["tests"]["host_unit_tests"].update(
            {
                "stdout_tail": host_stage.get("stdout_tail", ""),
                "stderr_tail": host_stage.get("stderr_tail", ""),
            }
        )

    integration_summary = raw_feedback.get("metrics", {}).get("integration", {})
    failed_scenarios = []
    for scenario in integration_summary.get("scenarios", []):
        if scenario.get("passed", True):
            continue
        failed_checks = sorted(
            check_name
            for check_name, check_passed in scenario.get("checks", {}).items()
            if check_passed is False
        )
        failed_scenario = {
            "name": scenario.get("name", "integration"),
            "reason": scenario.get("reason", "integration scenario failed"),
        }
        if failed_checks:
            failed_scenario["failed_checks"] = failed_checks
        for field_name in ("threshold_cross_ms", "timeout_off_ms", "timeout_off_delta_ms"):
            if scenario.get(field_name) is not None:
                failed_scenario[field_name] = scenario[field_name]
        observations = _failed_scenario_observations(scenario)
        if observations:
            failed_scenario["observations"] = observations
        failed_scenarios.append(failed_scenario)

    if feedback_config["include_error_details"]:
        view["build"]["errors"] = _clean_stage_messages(
            build_stage.get("errors", []),
            stage_success=bool(build_stage.get("success", False)),
        )
        view["run"]["errors"] = _clean_stage_messages(
            run_stage.get("errors", []),
            stage_success=bool(run_stage.get("success", False)),
            hide_json_fragments=True,
        )
        view["tests"]["integration"]["errors"] = (
            []
            if failed_scenarios
            else _clean_stage_messages(integration_stage.get("errors", []), hide_json_fragments=True)
        )

    if failed_scenarios:
        view["tests"]["integration"]["failed_scenarios"] = failed_scenarios

    if feedback_config["include_warnings"]:
        view["build"]["warnings"] = _clean_stage_messages(build_stage.get("warnings", []))

    if feedback_config["include_build_logs"]:
        view["build"]["stdout_tail"] = build_stage.get("stdout_tail", "")
        view["build"]["stderr_tail"] = build_stage.get("stderr_tail", "")

    if feedback_config["include_runtime_logs"]:
        view["run"]["stdout_tail"] = run_stage.get("stdout_tail", "")
        view["run"]["stderr_tail"] = run_stage.get("stderr_tail", "")
        view["tests"]["integration"]["stdout_tail"] = integration_stage.get("stdout_tail", "")
        view["tests"]["integration"]["stderr_tail"] = integration_stage.get("stderr_tail", "")

    if feedback_config["include_metrics"]:
        view["metrics"] = raw_feedback.get("metrics", {})

    if feedback_config["include_uart_transcript"]:
        view["uart"] = raw_feedback.get("uart", {})

    if feedback_config["include_trace_samples"]:
        view["traces"] = raw_feedback.get("traces", {})

    if feedback_config["include_history"]:
        view["history"] = raw_feedback.get("history", [])

    return _sanitize_value(view)


def _stage_status(payload: dict[str, Any]) -> str:
    if not payload.get("ran", False):
        return "NOT_RUN"
    return "PASS" if payload.get("success", False) else "FAIL"


def _format_stage_line(label: str, payload: dict[str, Any]) -> str:
    details = []
    if payload.get("return_code") is not None:
        details.append(f"code={payload['return_code']}")
    if payload.get("duration_s") is not None:
        details.append(f"duration={payload['duration_s']}s")
    suffix = f" ({', '.join(details)})" if details else ""
    return f"- {label}: {_stage_status(payload)}{suffix}"


def _append_list_section(lines: list[str], title: str, payload: list[str] | None) -> None:
    if not payload:
        return
    lines.extend(["", f"{title}:"])
    lines.extend(f"- {entry}" for entry in payload)


def _append_logs_section(lines: list[str], title: str, payload: dict[str, Any]) -> None:
    stdout_tail = payload.get("stdout_tail", "")
    stderr_tail = payload.get("stderr_tail", "")
    if not stdout_tail and not stderr_tail:
        return
    lines.extend(["", f"{title}:"])
    if stdout_tail:
        lines.extend(["stdout:", "```", stdout_tail, "```"])
    if stderr_tail:
        lines.extend(["stderr:", "```", stderr_tail, "```"])


def _append_failed_scenarios_section(lines: list[str], payload: list[dict[str, Any]] | None) -> None:
    if not payload:
        return

    lines.extend(["", "Failed integration scenarios:"])
    for scenario in payload:
        parts = [f"{scenario.get('name', 'integration')}: {scenario.get('reason', 'failed')}"]
        failed_checks = scenario.get("failed_checks") or []
        if failed_checks:
            parts.append(f"failed checks: {', '.join(failed_checks)}")
        if scenario.get("threshold_cross_ms") is not None:
            parts.append(f"threshold_cross_ms={scenario['threshold_cross_ms']}")
        if scenario.get("timeout_off_ms") is not None:
            parts.append(f"timeout_off_ms={scenario['timeout_off_ms']}")
        if scenario.get("timeout_off_delta_ms") is not None:
            parts.append(f"timeout_off_delta_ms={scenario['timeout_off_delta_ms']}")
        observations = scenario.get("observations") or []
        if observations:
            parts.append(f"observations: {' | '.join(observations)}")
        lines.append(f"- {'; '.join(parts)}")


def render_feedback_markdown(view: dict[str, Any]) -> str:
    summary = view.get("summary", {})
    tests = view.get("tests", {})
    build = view.get("build", {})
    upload = view.get("upload", {})
    run = view.get("run", {})
    host_tests = tests.get("host_unit_tests", {})
    integration = tests.get("integration", {})
    lines = [
        f"Status: {summary.get('status', 'UNKNOWN')}",
        f"Feedback mode: {view.get('feedback_mode', 'unknown')}",
        "",
        "Stages:",
        _format_stage_line("build", build),
        _format_stage_line("upload", upload),
        _format_stage_line("run", run),
        _format_stage_line("host unit tests", host_tests),
        _format_stage_line("integration", integration),
    ]

    if summary.get("failure_category"):
        lines.append(f"- failure category: {summary['failure_category']}")

    commentary = summary.get("commentary")
    if commentary:
        lines.extend(["", "Commentary:", commentary])

    _append_failed_scenarios_section(lines, integration.get("failed_scenarios"))

    for label, payload in (
        ("Host unit test errors", host_tests.get("errors")),
        ("Build errors", build.get("errors")),
        ("Run errors", run.get("errors")),
        ("Integration errors", integration.get("errors")),
    ):
        _append_list_section(lines, label, payload)

    for label, payload in (
        ("Host unit test warnings", host_tests.get("warnings")),
        ("Build warnings", build.get("warnings")),
    ):
        _append_list_section(lines, label, payload)

    for section_name in ("metrics", "uart", "traces", "history"):
        payload = view.get(section_name)
        if not payload:
            continue
        lines.extend(
            [
                "",
                f"{section_name.title()}:",
                "```json",
                json.dumps(payload, indent=2, sort_keys=True),
                "```",
            ]
        )

    for section_name, payload in (
        ("Host unit test logs", host_tests),
        ("Build logs", build),
        ("Run logs", run),
        ("Integration logs", integration),
    ):
        _append_logs_section(lines, section_name, payload)

    return "\n".join(lines) + "\n"
