from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TraceSample:
    timestamp_ms: int
    values: dict[str, Any]

    def to_json(self) -> dict[str, Any]:
        payload = {"timestamp_ms": self.timestamp_ms}
        payload.update(self.values)
        return payload


@dataclass
class ScenarioResult:
    name: str
    passed: bool
    reason: str
    checks: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    telemetry: dict[str, Any] = field(default_factory=dict)
    observations: list[str] = field(default_factory=list)
    trace_samples: list[TraceSample] = field(default_factory=list, repr=False)

    def to_json(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "passed": self.passed,
            "reason": self.reason,
            "trace_sample_count": len(self.trace_samples),
            "checks": self.checks,
            "metrics": self.metrics,
        }
        payload.update(self.telemetry)
        if self.observations:
            payload["observations"] = list(self.observations)
        return payload

