from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TankPlantConfig:
    tick_ms: int = 100
    fill_delta: int = 6
    drain_delta: int = 1
    min_level: int = 0
    max_level: int = 100


@dataclass
class TankPlant:
    level: int
    pump_on: bool = False
    now_ms: int = 0
    config: TankPlantConfig = field(default_factory=TankPlantConfig)

    def sense_frame(self) -> str:
        return f"SENSE LEVEL {self.level}"

    def apply_firmware_line(self, line: str) -> bool:
        normalized = line.strip()
        if normalized == "ACT PUMP ON":
            self.pump_on = True
            return True
        if normalized == "ACT PUMP OFF":
            self.pump_on = False
            return True
        return False

    def step(self) -> int:
        delta = (self.config.fill_delta if self.pump_on else 0) - self.config.drain_delta
        self.level = max(self.config.min_level, min(self.config.max_level, self.level + delta))
        self.now_ms += self.config.tick_ms
        return self.level

