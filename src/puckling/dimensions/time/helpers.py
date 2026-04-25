"""Time helpers — composable predicates plus a resolver.

Productions build `TimeData` values by composing the helpers below. The resolver
walks from a reference time to find the closest instant that satisfies the
data's predicate.

This intentionally stays small: workers porting Time rules can extend it as
needed via additional combinators in their own files (kept private to the
worker's locale).
"""

from __future__ import annotations

import datetime as dt

from puckling.dimensions.time.grain import Grain, add_grain, truncate
from puckling.dimensions.time.types import (
    InstantValue,
    IntervalDirection,
    IntervalValue,
    OpenIntervalValue,
    SingleTimeValue,
    TimeData,
    TimePredicate,
    TimeValue,
)

# ---------------------------------------------------------------------------
# Predicate builders


def always_true() -> TimePredicate:
    return lambda _d: True


def at_year(year: int) -> TimePredicate:
    return lambda d: d.year == year


def at_month(month: int) -> TimePredicate:
    return lambda d: d.month == month


def at_day_of_month(day: int) -> TimePredicate:
    return lambda d: d.day == day


def at_day_of_week(weekday: int) -> TimePredicate:
    """0 = Monday … 6 = Sunday (Python's `weekday()` semantics)."""
    return lambda d: d.weekday() == weekday


def at_hour(hour: int, *, is_12h: bool = False) -> TimePredicate:
    if is_12h:
        return lambda d: d.hour % 12 == hour % 12
    return lambda d: d.hour == hour


def at_minute(minute: int) -> TimePredicate:
    return lambda d: d.minute == minute


def intersect(*preds: TimePredicate) -> TimePredicate:
    return lambda d: all(p(d) for p in preds)


def union(*preds: TimePredicate) -> TimePredicate:
    return lambda d: any(p(d) for p in preds)


# ---------------------------------------------------------------------------
# TimeData factories


def time(
    predicate: TimePredicate,
    grain: Grain,
    *,
    latent: bool = False,
    holiday: str | None = None,
) -> TimeData:
    return TimeData(predicate=predicate, grain=grain, latent=latent, holiday=holiday)


def pinned_instant(value: dt.datetime, grain: Grain) -> TimeData:
    return TimeData(
        predicate=lambda d: d == value,
        grain=grain,
        pinned=InstantValue(value=value, grain=grain),
    )


def day_of_week(weekday: int) -> TimeData:
    return time(at_day_of_week(weekday), Grain.DAY)


def month(m: int) -> TimeData:
    return time(at_month(m), Grain.MONTH)


def year(y: int) -> TimeData:
    return time(at_year(y), Grain.YEAR)


def hour(h: int, *, is_12h: bool = False) -> TimeData:
    return time(at_hour(h, is_12h=is_12h), Grain.HOUR)


def hour_minute(h: int, m: int, *, is_12h: bool = False) -> TimeData:
    return time(intersect(at_hour(h, is_12h=is_12h), at_minute(m)), Grain.MINUTE)


# ---------------------------------------------------------------------------
# Resolver


_MAX_SCAN_STEPS = 366 * 5  # five years' worth of days


def _walk(
    start: dt.datetime,
    grain: Grain,
    predicate: TimePredicate,
    direction: int,
) -> dt.datetime | None:
    cur = truncate(start, grain)
    for _ in range(_MAX_SCAN_STEPS):
        if predicate(cur):
            return cur
        cur = add_grain(cur, grain, direction)
    return None


def resolve_time_data(td: TimeData, reference: dt.datetime) -> SingleTimeValue | None:
    """Find the nearest instant matching `td.predicate` relative to `reference`."""
    if td.pinned is not None:
        return td.pinned
    direction = td.direction
    if direction is IntervalDirection.BEFORE:
        instant = _walk(reference, td.grain, td.predicate, direction=-1)
    elif direction is IntervalDirection.AFTER:
        instant = _walk(reference, td.grain, td.predicate, direction=+1)
    else:
        # Default: pick the next future instant; if `not_immediate`, skip the current one.
        start = reference
        if td.not_immediate:
            start = add_grain(reference, td.grain, 1)
        instant = _walk(start, td.grain, td.predicate, direction=+1)
        if instant is None:
            instant = _walk(reference, td.grain, td.predicate, direction=-1)
    if instant is None:
        return None
    return InstantValue(value=instant, grain=td.grain)


def make_time_value(primary: SingleTimeValue, *, holiday: str | None = None) -> TimeValue:
    return TimeValue(primary=primary, holiday=holiday)


def make_interval(start: InstantValue, end: InstantValue) -> IntervalValue:
    return IntervalValue(start=start, end=end)


def make_open_interval(instant: InstantValue, direction: IntervalDirection) -> OpenIntervalValue:
    return OpenIntervalValue(instant=instant, direction=direction)
