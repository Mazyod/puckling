"""Computed dates used by holiday rules — Easter, Islamic dates, etc."""

from __future__ import annotations

import datetime as dt


def easter(year: int) -> dt.date:
    """Western Easter date for `year`, using Anonymous Gregorian (Meeus/Jones/Butcher)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    L = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * L) // 451
    month = (h + L - 7 * m + 114) // 31
    day = ((h + L - 7 * m + 114) % 31) + 1
    return dt.date(year, month, day)


def orthodox_easter(year: int) -> dt.date:
    """Eastern Orthodox Easter (Julian-based, converted to Gregorian)."""
    a = year % 4
    b = year % 7
    c = year % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    julian_month = (d + e + 114) // 31
    julian_day = ((d + e + 114) % 31) + 1
    julian = dt.date(year, julian_month, julian_day)
    # Julian → Gregorian offset: 13 days for the 1900-2099 range.
    return julian + dt.timedelta(days=13)
