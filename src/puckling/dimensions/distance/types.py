"""Distance value type."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DistanceUnit(Enum):
    KILOMETRE = "kilometre"
    METRE = "metre"
    CENTIMETRE = "centimetre"
    MILLIMETRE = "millimetre"
    MILE = "mile"
    YARD = "yard"
    FOOT = "foot"
    INCH = "inch"


@dataclass(frozen=True, slots=True)
class DistanceValue:
    value: float
    unit: DistanceUnit | None = None
    latent: bool = False

    def resolve(self, _context: object) -> dict:
        out = {"value": self.value, "type": "value"}
        if self.unit is not None:
            out["unit"] = self.unit.value
        return out


def distance(value: float, unit: DistanceUnit | None = None) -> DistanceValue:
    return DistanceValue(value=value, unit=unit)
