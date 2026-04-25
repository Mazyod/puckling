"""Duration value type."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from puckling.dimensions.time.grain import Grain


@dataclass(frozen=True, slots=True)
class NormalizedDuration:
    value: int
    unit: Literal["second"] = "second"


@dataclass(frozen=True, slots=True)
class DurationValue:
    """A duration: amount + grain (year/month/week/day/hour/minute/second)."""

    value: int
    grain: Grain
    latent: bool = False
    normalized: NormalizedDuration = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "normalized",
            NormalizedDuration(value=int(self.value * _SECONDS_PER_GRAIN[self.grain])),
        )

    def resolve(self, _context: object) -> DurationValue:
        return self


_SECONDS_PER_GRAIN = {
    Grain.SECOND: 1,
    Grain.MINUTE: 60,
    Grain.HOUR: 3600,
    Grain.DAY: 86_400,
    Grain.WEEK: 604_800,
    Grain.MONTH: 2_592_000,  # 30 days
    Grain.QUARTER: 7_776_000,
    Grain.YEAR: 31_536_000,
}


def duration(value: int, grain: Grain) -> DurationValue:
    return DurationValue(value=value, grain=grain)
