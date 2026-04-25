"""Private helpers for English Time rules.

The puckling foundation provides simple `TimeData` values whose `predicate`
selects matching instants relative to a reference time. That works well for
absolute time points (e.g. "January 5", "Monday", "5pm"), but many natural
phrases (e.g. "tomorrow", "in 3 days", "last week") need to compute their
result relative to the reference time at resolution time.

This module defines a richer `RelTime` value object that carries a
`compute(reference)` closure. The closure returns a `SingleTimeValue`
(`InstantValue` or `IntervalValue`) that gets surfaced as the resolved value.

Rule productions construct these using small builder helpers and combinators
inspired by Duckling's `Time/Helpers.hs` (e.g. `cycle_nth`, `pred_nth`,
`intersect`, `add_grain`, `make_interval`).
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

from puckling.dimensions.time.grain import Grain, add_grain, truncate
from puckling.dimensions.time.helpers import resolve_time_data
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

# Type aliases for the closures used by `RelTime`.
ComputeFn = Callable[[dt.datetime], SingleTimeValue | None]


@dataclass(frozen=True, slots=True, eq=False)
class RelTime:
    """A time value computed relative to a reference time.

    Attributes:
        compute: callable taking a reference `datetime` and returning a
            resolved single time value (instant or interval).
        grain: the natural grain of this value (used for surface formatting).
        latent: whether this value is latent (suppressed unless `with_latent`).
        holiday: optional holiday name to surface alongside the value.
        key: an opaque hashable identifier; rules that produce equivalent
            `RelTime` values use the same key so the saturating engine can
            dedupe them. (Closures are not naturally equal across rule firings,
            so we deduplicate on `key` instead.)
    """

    compute: ComputeFn
    grain: Grain
    latent: bool = False
    holiday: str | None = None
    key: tuple = ()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RelTime):
            return False
        return (
            self.key == other.key
            and self.grain == other.grain
            and self.latent == other.latent
            and self.holiday == other.holiday
        )

    def __hash__(self) -> int:
        return hash((self.key, self.grain, self.latent, self.holiday))

    def with_grain(self, g: Grain) -> RelTime:
        return replace(self, grain=g)

    def not_latent(self) -> RelTime:
        return replace(self, latent=False) if self.latent else self

    def resolve(self, context) -> TimeValue | None:
        value = self.compute(context.reference_time)
        if value is None:
            return None
        return TimeValue(primary=value, holiday=self.holiday)


# ---------------------------------------------------------------------------
# Constructors


def from_time_data(td: TimeData) -> RelTime:
    """Wrap a `TimeData` so it is resolved through the foundation's resolver."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        return resolve_time_data(td, ref)

    return RelTime(
        compute=go,
        grain=td.grain,
        latent=td.latent,
        holiday=td.holiday,
        key=("time_data", id(td)),
    )


def instant(value: dt.datetime, grain: Grain, *, holiday: str | None = None) -> RelTime:
    inst = InstantValue(value=value, grain=grain)

    def go(_ref: dt.datetime) -> SingleTimeValue | None:
        return inst

    return RelTime(
        compute=go,
        grain=grain,
        holiday=holiday,
        key=("instant", value.isoformat(), grain.value),
    )


def now() -> RelTime:
    def go(ref: dt.datetime) -> SingleTimeValue | None:
        return InstantValue(value=truncate(ref, Grain.SECOND), grain=Grain.SECOND)

    return RelTime(compute=go, grain=Grain.SECOND, key=("now",))


def today() -> RelTime:
    return relative_day_offset(0)


def relative_day_offset(n: int) -> RelTime:
    """A specific day, n days from the reference (0 = today, 1 = tomorrow, ...)."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        d = truncate(ref, Grain.DAY) + dt.timedelta(days=n)
        return InstantValue(value=d, grain=Grain.DAY)

    return RelTime(compute=go, grain=Grain.DAY, key=("rel_day", n))


def cycle_nth(grain: Grain, n: int) -> RelTime:
    """Mirrors Duckling's `cycleNth grain n` — the n-th period of `grain` from now.

    `n == 0` is "this <grain>" (current period), `n == 1` is the next period,
    `n == -1` is the previous period.
    """

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        start = truncate(ref, grain)
        return InstantValue(value=add_grain(start, grain, n), grain=grain)

    return RelTime(compute=go, grain=grain, key=("cycle_nth", grain.value, n))


def fixed_year(year: int) -> RelTime:
    def go(_ref: dt.datetime) -> SingleTimeValue | None:
        # TODO(puckling): edge case — Python's datetime rejects BC years (<1).
        if year < 1 or year > 9999:
            return None
        return InstantValue(
            value=dt.datetime(year, 1, 1, tzinfo=dt.UTC),
            grain=Grain.YEAR,
        )

    return RelTime(compute=go, grain=Grain.YEAR, key=("fixed_year", year))


def year_month(year: int, month: int) -> RelTime:
    def go(_ref: dt.datetime) -> SingleTimeValue | None:
        return InstantValue(
            value=dt.datetime(year, month, 1, tzinfo=dt.UTC),
            grain=Grain.MONTH,
        )

    return RelTime(compute=go, grain=Grain.MONTH, key=("year_month", year, month))


def year_month_day(year: int, month: int, day: int) -> RelTime:
    def go(_ref: dt.datetime) -> SingleTimeValue | None:
        return InstantValue(
            value=dt.datetime(year, month, day, tzinfo=dt.UTC),
            grain=Grain.DAY,
        )

    return RelTime(
        compute=go,
        grain=Grain.DAY,
        key=("year_month_day", year, month, day),
    )


# ---------------------------------------------------------------------------
# Predicate-based builders that find the nearest matching instant


def _walk_predicate(
    start: dt.datetime,
    grain: Grain,
    predicate: TimePredicate,
    direction: int,
    *,
    max_steps: int = 366 * 5,
) -> dt.datetime | None:
    cur = truncate(start, grain)
    for _ in range(max_steps):
        if predicate(cur):
            return cur
        cur = add_grain(cur, grain, direction)
    return None


def find_next(
    predicate: TimePredicate,
    grain: Grain,
    *,
    future: bool = True,
    key: tuple = (),
) -> RelTime:
    """Find the next (or previous) instant from the reference matching predicate."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        direction = 1 if future else -1
        d = _walk_predicate(ref, grain, predicate, direction)
        if d is None:
            return None
        if d.tzinfo is None and ref.tzinfo is not None:
            d = d.replace(tzinfo=ref.tzinfo)
        return InstantValue(value=d, grain=grain)

    return RelTime(compute=go, grain=grain, key=("find_next", future, key))


def find_strict_next(predicate: TimePredicate, grain: Grain, *, key: tuple = ()) -> RelTime:
    """Skip the current period if it already matches; pick the strictly next match."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        start = add_grain(truncate(ref, grain), grain, 1)
        d = _walk_predicate(start, grain, predicate, 1)
        if d is None:
            return None
        if d.tzinfo is None and ref.tzinfo is not None:
            d = d.replace(tzinfo=ref.tzinfo)
        return InstantValue(value=d, grain=grain)

    return RelTime(compute=go, grain=grain, key=("find_strict_next", key))


# ---------------------------------------------------------------------------
# Day-of-week / month / time-of-day


def day_of_week_relative(weekday: int, *, this_week: bool = False) -> RelTime:
    """Return the next occurrence of the given weekday (0=Monday).

    Duckling treats a bare weekday as the next strict future occurrence —
    today does not satisfy. This matches the corpus expectation that
    "tuesday" (with reference Tuesday) resolves to next Tuesday, not today.
    """

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        ref_day = truncate(ref, Grain.DAY)
        delta = (weekday - ref_day.weekday()) % 7
        if this_week:
            # "Monday of this week" — Monday in the same ISO week.
            week_start = ref_day - dt.timedelta(days=ref_day.weekday())
            target = week_start + dt.timedelta(days=weekday)
        else:
            if delta == 0:
                delta = 7
            target = ref_day + dt.timedelta(days=delta)
        return InstantValue(value=target, grain=Grain.DAY)

    return RelTime(compute=go, grain=Grain.DAY, key=("dow_rel", weekday, this_week))


def next_day_of_week(weekday: int) -> RelTime:
    """The next strict occurrence of weekday (in the next ISO week)."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        ref_day = truncate(ref, Grain.DAY)
        # Move to next week, then to the target weekday.
        days_to_next_monday = 7 - ref_day.weekday()
        next_week_start = ref_day + dt.timedelta(days=days_to_next_monday)
        target = next_week_start + dt.timedelta(days=weekday)
        return InstantValue(value=target, grain=Grain.DAY)

    return RelTime(compute=go, grain=Grain.DAY, key=("next_dow", weekday))


def last_day_of_week(weekday: int) -> RelTime:
    """The most recent prior occurrence of `weekday` (strictly before today)."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        ref_day = truncate(ref, Grain.DAY)
        delta = (ref_day.weekday() - weekday) % 7
        if delta == 0:
            delta = 7
        target = ref_day - dt.timedelta(days=delta)
        return InstantValue(value=target, grain=Grain.DAY)

    return RelTime(compute=go, grain=Grain.DAY, key=("last_dow", weekday))


def named_month(month: int) -> RelTime:
    """The named month, year-agnostic — picks the nearest occurrence."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        # If we're past the month this year, return next year's; otherwise this year's.
        year = ref.year if ref.month <= month else ref.year + 1
        return InstantValue(
            value=dt.datetime(year, month, 1, tzinfo=ref.tzinfo),
            grain=Grain.MONTH,
        )

    return RelTime(compute=go, grain=Grain.MONTH, key=("named_month", month))


def month_day(month: int, day: int, *, holiday: str | None = None) -> RelTime:
    """A specific (month, day) — picks the nearest future occurrence."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        year = ref.year
        try:
            cand = dt.datetime(year, month, day, tzinfo=ref.tzinfo)
        except ValueError:
            return None
        ref_day = truncate(ref, Grain.DAY)
        if cand < ref_day:
            cand = cand.replace(year=year + 1)
        return InstantValue(value=cand, grain=Grain.DAY)

    return RelTime(
        compute=go,
        grain=Grain.DAY,
        holiday=holiday,
        key=("month_day", month, day, holiday),
    )


def _clock_value(
    h: int, m: int, s: int, is_12h: bool, grain: Grain
) -> ComputeFn:
    """Closure that finds the nearest future instant matching (h, m, s)."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        ref_at_grain = truncate(ref, grain)
        target_hours = (h % 12, h % 12 + 12) if is_12h else (h,)
        candidates: list[dt.datetime] = []
        for th in target_hours:
            cur = ref_at_grain.replace(hour=th, minute=m, second=s)
            # If the candidate already passed (or equals the truncated ref but
            # the actual ref is finer), roll forward by a day.
            if cur < ref_at_grain or (cur == ref_at_grain and ref > ref_at_grain):
                cur += dt.timedelta(days=1)
            candidates.append(cur)
        return InstantValue(value=min(candidates), grain=grain)

    return go


def hour_value(h: int, is_12h: bool, *, latent: bool = False) -> RelTime:
    """A clock hour-of-day — picks the next matching hour from the reference."""
    return RelTime(
        compute=_clock_value(h, 0, 0, is_12h, Grain.HOUR),
        grain=Grain.HOUR,
        latent=latent,
        key=("hour", h, is_12h),
    )


def hour_minute_value(h: int, m: int, is_12h: bool, *, latent: bool = False) -> RelTime:
    return RelTime(
        compute=_clock_value(h, m, 0, is_12h, Grain.MINUTE),
        grain=Grain.MINUTE,
        latent=latent,
        key=("hour_minute", h, m, is_12h),
    )


def hour_minute_second_value(h: int, m: int, s: int, is_12h: bool) -> RelTime:
    return RelTime(
        compute=_clock_value(h, m, s, is_12h, Grain.SECOND),
        grain=Grain.SECOND,
        key=("hms", h, m, s, is_12h),
    )


# ---------------------------------------------------------------------------
# Intersections / shifts


def shift_minutes(rt: RelTime, minutes: int) -> RelTime:
    """Add minutes to the resolved instant of `rt`, keeping the grain."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        v = rt.compute(ref)
        if not isinstance(v, InstantValue):
            return None
        return InstantValue(value=v.value + dt.timedelta(minutes=minutes), grain=Grain.MINUTE)

    return RelTime(
        compute=go,
        grain=Grain.MINUTE,
        latent=rt.latent,
        holiday=rt.holiday,
        key=("shift_minutes", rt.key, minutes),
    )


def shift_grain(rt: RelTime, grain: Grain, n: int) -> RelTime:
    """Shift `rt` by `n` units of `grain`."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        v = rt.compute(ref)
        if not isinstance(v, InstantValue):
            return None
        new_value = add_grain(v.value, grain, n)
        return InstantValue(value=new_value, grain=v.grain)

    return RelTime(
        compute=go,
        grain=rt.grain,
        latent=rt.latent,
        holiday=rt.holiday,
        key=("shift_grain", rt.key, grain.value, n),
    )


def at_year_in(rt: RelTime, year: int) -> RelTime:
    """Same month/day as `rt`, but anchored to `year`."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        v = rt.compute(ref)
        if not isinstance(v, InstantValue):
            return None
        try:
            new_value = v.value.replace(year=year)
        except ValueError:
            return None
        return InstantValue(value=new_value, grain=v.grain)

    return RelTime(
        compute=go,
        grain=rt.grain,
        holiday=rt.holiday,
        key=("at_year_in", rt.key, year),
    )


def with_day_of_month(rt: RelTime, day: int) -> RelTime:
    """Replace the day-of-month of the resolved value (used to combine month + day)."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        v = rt.compute(ref)
        if not isinstance(v, InstantValue):
            return None
        try:
            new_value = v.value.replace(day=day)
        except ValueError:
            return None
        return InstantValue(value=new_value, grain=Grain.DAY)

    return RelTime(
        compute=go,
        grain=Grain.DAY,
        holiday=rt.holiday,
        key=("with_dom", rt.key, day),
    )


def at_time_of_day(rt: RelTime, hour: int, minute: int = 0) -> RelTime:
    """Anchor `rt` (a day-grain value) to a specific time of day."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        v = rt.compute(ref)
        if not isinstance(v, InstantValue):
            return None
        new_value = v.value.replace(hour=hour, minute=minute, second=0, microsecond=0)
        finer = Grain.MINUTE if minute else Grain.HOUR
        return InstantValue(value=new_value, grain=finer)

    return RelTime(
        compute=go,
        grain=Grain.HOUR if minute == 0 else Grain.MINUTE,
        holiday=rt.holiday,
        key=("at_tod", rt.key, hour, minute),
    )


# ---------------------------------------------------------------------------
# Intervals


def interval(start: RelTime, end: RelTime, *, holiday: str | None = None) -> RelTime:
    """Build an interval from two RelTime endpoints.

    The end is treated as exclusive — Duckling's "Open" interval semantics.
    The grain of the interval is the finer of the two endpoint grains.
    """

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        s = start.compute(ref)
        e = end.compute(ref)
        if not isinstance(s, InstantValue) or not isinstance(e, InstantValue):
            return None
        return IntervalValue(start=s, end=e)

    finer = start.grain if start.grain.rank <= end.grain.rank else end.grain
    return RelTime(
        compute=go,
        grain=finer,
        holiday=holiday or start.holiday or end.holiday,
        key=("interval", start.key, end.key, holiday),
    )


def interval_grain(start: RelTime, grain: Grain, n: int) -> RelTime:
    """Build an interval covering `n` cycles of `grain` starting at `start`."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        s = start.compute(ref)
        if not isinstance(s, InstantValue):
            return None
        e = InstantValue(value=add_grain(s.value, grain, n), grain=grain)
        return IntervalValue(start=s, end=e)

    return RelTime(
        compute=go,
        grain=grain,
        key=("interval_grain", start.key, grain.value, n),
    )


def open_interval(rt: RelTime, direction: IntervalDirection) -> RelTime:
    """Build an open-ended interval bounded on one side by `rt`."""

    def go(ref: dt.datetime) -> SingleTimeValue | None:
        v = rt.compute(ref)
        if not isinstance(v, InstantValue):
            return None
        return OpenIntervalValue(instant=v, direction=direction)

    return RelTime(
        compute=go,
        grain=rt.grain,
        holiday=rt.holiday,
        key=("open_interval", rt.key, direction.value),
    )


# ---------------------------------------------------------------------------
# Token helpers


def get_int_value(value: Any) -> int | None:
    """Extract an integer value from a numeral or ordinal token value."""
    v = getattr(value, "value", None)
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return None
