"""Time grain — Duckling's `Grain` enum, plus arithmetic helpers."""

from __future__ import annotations

import datetime as dt
from enum import Enum


class Grain(Enum):
    """Granularity of a time value, from coarsest to finest."""

    YEAR = "year"
    QUARTER = "quarter"
    MONTH = "month"
    WEEK = "week"
    DAY = "day"
    HOUR = "hour"
    MINUTE = "minute"
    SECOND = "second"

    @property
    def rank(self) -> int:
        """Higher rank = coarser grain."""
        return _RANK[self]

    def is_coarser_than(self, other: Grain) -> bool:
        return self.rank > other.rank


_RANK = {
    Grain.YEAR: 7,
    Grain.QUARTER: 6,
    Grain.MONTH: 5,
    Grain.WEEK: 4,
    Grain.DAY: 3,
    Grain.HOUR: 2,
    Grain.MINUTE: 1,
    Grain.SECOND: 0,
}


def add_grain(d: dt.datetime, grain: Grain, n: int) -> dt.datetime:
    """Add `n * grain` to `d`, returning a new datetime."""
    if grain is Grain.SECOND:
        return d + dt.timedelta(seconds=n)
    if grain is Grain.MINUTE:
        return d + dt.timedelta(minutes=n)
    if grain is Grain.HOUR:
        return d + dt.timedelta(hours=n)
    if grain is Grain.DAY:
        return d + dt.timedelta(days=n)
    if grain is Grain.WEEK:
        return d + dt.timedelta(weeks=n)
    if grain is Grain.MONTH:
        return _add_months(d, n)
    if grain is Grain.QUARTER:
        return _add_months(d, n * 3)
    if grain is Grain.YEAR:
        return _add_months(d, n * 12)
    raise ValueError(f"unknown grain: {grain}")


def _add_months(d: dt.datetime, n: int) -> dt.datetime:
    month0 = d.month - 1 + n
    year = d.year + month0 // 12
    month = month0 % 12 + 1
    day = min(d.day, _days_in_month(year, month))
    return d.replace(year=year, month=month, day=day)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    return (dt.date(year + (month // 12), (month % 12) + 1, 1) - dt.date(year, month, 1)).days


def truncate(d: dt.datetime, grain: Grain) -> dt.datetime:
    """Round `d` down to the start of the given `grain`."""
    if grain is Grain.SECOND:
        return d.replace(microsecond=0)
    if grain is Grain.MINUTE:
        return d.replace(second=0, microsecond=0)
    if grain is Grain.HOUR:
        return d.replace(minute=0, second=0, microsecond=0)
    if grain is Grain.DAY:
        return d.replace(hour=0, minute=0, second=0, microsecond=0)
    if grain is Grain.WEEK:
        # ISO week starts on Monday.
        d0 = truncate(d, Grain.DAY)
        return d0 - dt.timedelta(days=d0.weekday())
    if grain is Grain.MONTH:
        return d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if grain is Grain.QUARTER:
        m = ((d.month - 1) // 3) * 3 + 1
        return d.replace(month=m, day=1, hour=0, minute=0, second=0, microsecond=0)
    if grain is Grain.YEAR:
        return d.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"unknown grain: {grain}")
