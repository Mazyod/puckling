"""Temperature value type."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TemperatureUnit(Enum):
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"
    KELVIN = "kelvin"
    DEGREE = "degree"


@dataclass(frozen=True, slots=True)
class TemperatureValue:
    value: float
    unit: TemperatureUnit | None = None
    latent: bool = False

    def resolve(self, _context: object) -> dict:
        out = {"value": self.value, "type": "value"}
        if self.unit is not None:
            out["unit"] = self.unit.value
        return out


def temperature(value: float, unit: TemperatureUnit | None = None) -> TemperatureValue:
    return TemperatureValue(value=value, unit=unit)
