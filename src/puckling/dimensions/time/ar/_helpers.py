"""AR-local time combinators — reference-relative day offsets and Hijri tables.

Foundation `TimeData` resolves predicates by walking forward/backward from the
reference time, which fits "next Friday" but not "today / tomorrow / yesterday"
(those need an offset *from* the reference, regardless of weekday). This module
defines a small value class with its own `resolve(context)` so the AR rules can
return tokens that compute their date at resolution time.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass

from puckling.dimensions.time.grain import Grain, add_grain, truncate
from puckling.dimensions.time.helpers import resolve_time_data
from puckling.dimensions.time.types import InstantValue, TimeData, TimeValue


@dataclass(frozen=True, slots=True)
class WrappedTimeData:
    """Foundation `TimeData` wrapped so `resolve()` produces a full `TimeValue` dict.

    Foundation `TimeData.resolve` returns the raw `InstantValue.to_dict()`, which
    lacks the top-level `type: value` key the AR corpus expects. Tokens emitted
    by AR rules wrap their `TimeData` in this class instead.
    """

    inner: TimeData

    @property
    def grain(self) -> Grain:
        return self.inner.grain

    @property
    def latent(self) -> bool:
        return self.inner.latent

    def resolve(self, context) -> dict:
        instant = resolve_time_data(self.inner, context.reference_time)
        if instant is None:
            return {}
        return TimeValue(primary=instant, holiday=self.inner.holiday).to_dict()


@dataclass(frozen=True, slots=True)
class RelativeDayTime:
    """Day-grained value computed as `reference + offset days` at resolve-time."""

    offset_days: int
    grain: Grain = Grain.DAY
    latent: bool = False

    def resolve(self, context) -> dict:
        anchor = truncate(context.reference_time, Grain.DAY)
        moment = anchor + dt.timedelta(days=self.offset_days)
        return TimeValue(primary=InstantValue(value=moment, grain=self.grain)).to_dict()


@dataclass(frozen=True, slots=True)
class TimeOfDayValue:
    """A wall-clock time anchored to the reference date.

    Mirrors Duckling's behaviour where "3:18" resolves to today's 03:18 even if
    it's already past — `_walk`'s forward-only search would otherwise skip to
    tomorrow.
    """

    hour: int
    minute: int
    latent: bool = False
    grain: Grain = Grain.MINUTE

    def resolve(self, context) -> dict:
        moment = context.reference_time.replace(
            hour=self.hour, minute=self.minute, second=0, microsecond=0
        )
        return TimeValue(primary=InstantValue(value=moment, grain=self.grain)).to_dict()


@dataclass(frozen=True, slots=True)
class RelativeGrainTime:
    """Grain-aligned value computed as `truncate(reference, grain) + n` at resolve-time.

    Mirrors Duckling's `cycleNth grain n`: end-of-month becomes "this month, +1
    months" and so on.
    """

    grain: Grain
    offset: int
    latent: bool = False

    def resolve(self, context) -> dict:
        anchor = truncate(context.reference_time, self.grain)
        moment = add_grain(anchor, self.grain, self.offset)
        return TimeValue(primary=InstantValue(value=moment, grain=self.grain)).to_dict()


@dataclass(frozen=True, slots=True)
class HolidayValue:
    """A holiday whose date is looked up by year, resolved to the next occurrence."""

    name: str
    table: Callable[[int], dt.date | None]
    grain: Grain = Grain.DAY
    latent: bool = False

    def resolve(self, context) -> dict:
        ref = context.reference_time
        ref_date = ref.date()
        for candidate_year in (ref.year, ref.year + 1):
            target = self.table(candidate_year)
            if target is None or target < ref_date:
                continue
            target_dt = dt.datetime(
                target.year, target.month, target.day, tzinfo=ref.tzinfo
            )
            primary = InstantValue(value=target_dt, grain=Grain.DAY)
            return TimeValue(primary=primary, holiday=self.name).to_dict()
        return {}


# ---------------------------------------------------------------------------
# Hijri-anchored holidays — explicit table, no library dependency.
#
# Dates from public almanacs (Umm al-Qura / civil observance). Coverage spans
# 2010–2030; outside that range we return None so the resolver simply omits a
# match instead of guessing.

_EID_AL_FITR: dict[int, dt.date] = {
    2010: dt.date(2010, 9, 10),
    2011: dt.date(2011, 8, 30),
    2012: dt.date(2012, 8, 19),
    2013: dt.date(2013, 8, 8),
    2014: dt.date(2014, 7, 28),
    2015: dt.date(2015, 7, 17),
    2016: dt.date(2016, 7, 6),
    2017: dt.date(2017, 6, 25),
    2018: dt.date(2018, 6, 15),
    2019: dt.date(2019, 6, 4),
    2020: dt.date(2020, 5, 24),
    2021: dt.date(2021, 5, 13),
    2022: dt.date(2022, 5, 2),
    2023: dt.date(2023, 4, 21),
    2024: dt.date(2024, 4, 10),
    2025: dt.date(2025, 3, 30),
    2026: dt.date(2026, 3, 20),
    2027: dt.date(2027, 3, 9),
    2028: dt.date(2028, 2, 26),
    2029: dt.date(2029, 2, 14),
    2030: dt.date(2030, 2, 4),
}

_EID_AL_ADHA: dict[int, dt.date] = {
    2010: dt.date(2010, 11, 16),
    2011: dt.date(2011, 11, 6),
    2012: dt.date(2012, 10, 26),
    2013: dt.date(2013, 10, 15),
    2014: dt.date(2014, 10, 4),
    2015: dt.date(2015, 9, 23),
    2016: dt.date(2016, 9, 12),
    2017: dt.date(2017, 9, 1),
    2018: dt.date(2018, 8, 21),
    2019: dt.date(2019, 8, 11),
    2020: dt.date(2020, 7, 31),
    2021: dt.date(2021, 7, 20),
    2022: dt.date(2022, 7, 9),
    2023: dt.date(2023, 6, 28),
    2024: dt.date(2024, 6, 16),
    2025: dt.date(2025, 6, 6),
    2026: dt.date(2026, 5, 27),
    2027: dt.date(2027, 5, 16),
    2028: dt.date(2028, 5, 5),
    2029: dt.date(2029, 4, 24),
    2030: dt.date(2030, 4, 13),
}

# 1 Muharram (Islamic New Year) — civil observance.
_MUHARRAM_1: dict[int, dt.date] = {
    2010: dt.date(2010, 12, 7),
    2011: dt.date(2011, 11, 26),
    2012: dt.date(2012, 11, 15),
    2013: dt.date(2013, 11, 4),
    2014: dt.date(2014, 10, 25),
    2015: dt.date(2015, 10, 14),
    2016: dt.date(2016, 10, 2),
    2017: dt.date(2017, 9, 21),
    2018: dt.date(2018, 9, 11),
    2019: dt.date(2019, 8, 31),
    2020: dt.date(2020, 8, 20),
    2021: dt.date(2021, 8, 9),
    2022: dt.date(2022, 7, 30),
    2023: dt.date(2023, 7, 19),
    2024: dt.date(2024, 7, 7),
    2025: dt.date(2025, 6, 26),
    2026: dt.date(2026, 6, 16),
    2027: dt.date(2027, 6, 5),
    2028: dt.date(2028, 5, 25),
    2029: dt.date(2029, 5, 14),
    2030: dt.date(2030, 5, 3),
}


def eid_al_fitr(year: int) -> dt.date | None:
    return _EID_AL_FITR.get(year)


def eid_al_adha(year: int) -> dt.date | None:
    return _EID_AL_ADHA.get(year)


def muharram(year: int) -> dt.date | None:
    return _MUHARRAM_1.get(year)
