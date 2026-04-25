"""Volume value type."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VolumeUnit(Enum):
    LITRE = "litre"
    MILLILITRE = "millilitre"
    GALLON = "gallon"
    QUART = "quart"
    PINT = "pint"
    CUP = "cup"
    FLUID_OUNCE = "fluid-ounce"
    HECTOLITRE = "hectolitre"


@dataclass(frozen=True, slots=True)
class VolumeValue:
    value: float
    unit: VolumeUnit | None = None
    latent: bool = False

    def resolve(self, _context: object) -> dict:
        out = {"value": self.value, "type": "value"}
        if self.unit is not None:
            out["unit"] = self.unit.value
        return out


def volume(value: float, unit: VolumeUnit | None = None) -> VolumeValue:
    return VolumeValue(value=value, unit=unit)
