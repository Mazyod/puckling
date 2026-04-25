"""Helpers for holiday rules — recurring fixed-date and computed dates.

Workers porting holiday rules can use `fixed_holiday(month, day, name)` for
fixed-date holidays (e.g. New Year's Day) and `computed_holiday(name, fn)` for
holidays whose date is computed (e.g. Easter, Eid). The `fn` returns the
holiday's date for a given year.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable

from puckling.dimensions.time.grain import Grain
from puckling.dimensions.time.helpers import at_day_of_month, at_month, intersect, time
from puckling.dimensions.time.types import TimeData


def fixed_holiday(month: int, day: int, name: str) -> TimeData:
    """A recurring holiday on a fixed (month, day) every year."""
    return time(
        intersect(at_month(month), at_day_of_month(day)),
        Grain.DAY,
        holiday=name,
    )


def computed_holiday(name: str, date_for: Callable[[int], dt.date]) -> TimeData:
    """A recurring holiday whose date is computed per year by `date_for`."""

    def predicate(d: dt.datetime) -> bool:
        target = date_for(d.year)
        return d.year == target.year and d.month == target.month and d.day == target.day

    return time(predicate, Grain.DAY, holiday=name)
