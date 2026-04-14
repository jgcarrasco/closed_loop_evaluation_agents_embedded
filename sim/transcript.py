from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class TranscriptEvent:
    timestamp_s: float
    direction: str
    payload: str

    def render(self) -> str:
        return f"{self.timestamp_s:0.3f} {self.direction} {self.payload}".rstrip()


@dataclass
class Transcript:
    events: list[TranscriptEvent] = field(default_factory=list)

    def record(self, timestamp_s: float, direction: str, payload: str) -> None:
        self.events.append(
            TranscriptEvent(
                timestamp_s=timestamp_s,
                direction=direction,
                payload=payload.rstrip("\r\n"),
            )
        )

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        rendered = "\n".join(event.render() for event in self.events)
        if rendered:
            rendered += "\n"
        path.write_text(rendered, encoding="ascii")

