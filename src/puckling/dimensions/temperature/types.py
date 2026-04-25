"""Temperature value type."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TemperatureUnit(Enum):
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"
    KELVIN = "kelvin"
    DEGREE = "degree"


class TemperatureIntervalDirection(Enum):
    ABOVE = "above"
    UNDER = "under"


@dataclass(frozen=True, slots=True)
class TemperatureValue:
    value: float
    unit: TemperatureUnit | None = None
    latent: bool = False

    def resolve(self, _context: object) -> TemperatureValue:
        return self


@dataclass(frozen=True, slots=True)
class TemperatureIntervalValue:
    start: TemperatureValue
    end: TemperatureValue
    latent: bool = False

    def resolve(self, _context: object) -> TemperatureIntervalValue:
        return self


@dataclass(frozen=True, slots=True)
class TemperatureOpenIntervalValue:
    bound: TemperatureValue
    direction: TemperatureIntervalDirection
    latent: bool = False

    def resolve(self, _context: object) -> TemperatureOpenIntervalValue:
        return self


def temperature(value: float, unit: TemperatureUnit | None = None) -> TemperatureValue:
    return TemperatureValue(value=value, unit=unit)
