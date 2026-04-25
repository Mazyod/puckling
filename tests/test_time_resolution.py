"""Time-resolution arithmetic edge tests.

Locks in correct behavior at leap years, year boundaries, month-end clamps,
weekday ambiguities, and similar edges that upstream Duckling glosses over.

Each test builds a custom `Context` with a tricky `reference_time` and asserts
that `parse(phrase, ctx)` resolves to the expected date/time/grain. Where
puckling's current behavior differs from a naive expectation, the test locks
in the *actual* behavior and documents the convention; bug-suspect cases use
``# TODO(puckling): edge case`` plus ``@pytest.mark.xfail``.
"""

from __future__ import annotations

import datetime as dt

import pytest

from puckling import Context, Locale, Options, parse
from puckling.locale import Lang


def _ctx_en(year: int, month: int, day: int, hour: int = 12, minute: int = 0) -> Context:
    return Context(
        reference_time=dt.datetime(year, month, day, hour, minute, tzinfo=dt.UTC),
        locale=Locale(Lang.EN),
    )


def _time_value(entities) -> dict | None:
    """Return the first time-dim entity's value dict, or None."""
    for e in entities:
        if e.dim == "time":
            return e.value
    return None


def _parse_time(phrase: str, ctx: Context) -> dict | None:
    return _time_value(parse(phrase, ctx, Options(), dims=("time",)))


# ---------------------------------------------------------------------------
# 1. Leap year (reference 2024-02-29)


def test_leap_year_tomorrow():
    """2024-02-29 + 1 day = 2024-03-01 (no Feb 30)."""
    value = _parse_time("tomorrow", _ctx_en(2024, 2, 29))
    assert value is not None
    assert value["value"].startswith("2024-03-01")
    assert value["grain"] == "day"


def test_leap_year_in_365_days():
    """365 days after 2024-02-29 lands on 2025-02-28 (2024 is a leap year, 2025 is not)."""
    value = _parse_time("in 365 days", _ctx_en(2024, 2, 29))
    assert value is not None
    # Grain comes back as 'hour' for "in N days" (preserves reference clock).
    assert value["value"].startswith("2025-02-28")
    assert value["grain"] == "hour"


def test_leap_year_in_1_year_clamps_to_feb_month():
    """"in 1 year" from a leap day resolves to month-grain Feb 2025.

    Puckling's `_offset_now` truncates year/month shifts to the start of the
    month, so the resolver returns 2025-02-01 with grain=month rather than the
    clamped Feb 28. Lock the convention in here.
    """
    value = _parse_time("in 1 year", _ctx_en(2024, 2, 29))
    assert value is not None
    assert value["value"] == "2025-02-01T00:00:00+00:00"
    assert value["grain"] == "month"


# ---------------------------------------------------------------------------
# 2. Year boundary forward (reference 2023-12-31 23:00)


def test_year_boundary_forward_tomorrow():
    """2023-12-31 + 1 day = 2024-01-01."""
    value = _parse_time("tomorrow", _ctx_en(2023, 12, 31, 23, 0))
    assert value is not None
    assert value["value"].startswith("2024-01-01")
    assert value["grain"] == "day"


def test_year_boundary_forward_in_1_hour():
    """2023-12-31 23:00 + 1 hour = 2024-01-01 00:00."""
    value = _parse_time("in 1 hour", _ctx_en(2023, 12, 31, 23, 0))
    assert value is not None
    assert value["value"] == "2024-01-01T00:00:00+00:00"
    assert value["grain"] == "minute"


# ---------------------------------------------------------------------------
# 3. Year boundary backward (reference 2024-01-01 01:00)


def test_year_boundary_backward_yesterday():
    """2024-01-01 - 1 day = 2023-12-31."""
    value = _parse_time("yesterday", _ctx_en(2024, 1, 1, 1, 0))
    assert value is not None
    assert value["value"].startswith("2023-12-31")
    assert value["grain"] == "day"


def test_year_boundary_backward_1_hour_ago():
    """2024-01-01 01:00 - 1 hour = 2024-01-01 00:00 (does not roll into prev year)."""
    value = _parse_time("1 hour ago", _ctx_en(2024, 1, 1, 1, 0))
    assert value is not None
    assert value["value"] == "2024-01-01T00:00:00+00:00"
    assert value["grain"] == "minute"


# ---------------------------------------------------------------------------
# 4. Month-end "next month" — cycle returns the *start* of the next month


def test_next_month_from_jan_31_leap_year():
    """`next month` from 2024-01-31 returns 2024-02-01 (start of next cycle).

    `cycle_nth` returns the truncated start of the period (month-grain), not a
    clamped day-grain instant — so there is no Feb-29 vs. Feb-28 distinction.
    """
    value = _parse_time("next month", _ctx_en(2024, 1, 31))
    assert value is not None
    assert value["value"] == "2024-02-01T00:00:00+00:00"
    assert value["grain"] == "month"


def test_next_month_from_jan_31_non_leap_year():
    """Same as above, but 2023 is not a leap year — still 2023-02-01 month-grain."""
    value = _parse_time("next month", _ctx_en(2023, 1, 31))
    assert value is not None
    assert value["value"] == "2023-02-01T00:00:00+00:00"
    assert value["grain"] == "month"


# ---------------------------------------------------------------------------
# 5. Same-day-of-week ambiguity (reference Tue 2013-02-12)


def test_bare_weekday_on_same_weekday_skips_to_next():
    """A bare "Tuesday" on a Tuesday resolves to *next* Tuesday, not today.

    Duckling treats a bare weekday as a strict-future occurrence; this is the
    documented convention in `day_of_week_relative`.
    """
    value = _parse_time("Tuesday", _ctx_en(2013, 2, 12))
    assert value is not None
    assert value["value"].startswith("2013-02-19")
    assert value["grain"] == "day"


def test_this_weekday_on_same_weekday_also_skips():
    """"this Tuesday" on a Tuesday currently resolves to *next* Tuesday.

    Lock in this behavior so we notice if it ever changes (Duckling-ish
    convention treats "this <weekday>" identically to a bare weekday).
    """
    value = _parse_time("this Tuesday", _ctx_en(2013, 2, 12))
    assert value is not None
    assert value["value"].startswith("2013-02-19")
    assert value["grain"] == "day"


# ---------------------------------------------------------------------------
# 6. "Next Monday" on Sunday (reference Sun 2013-02-10)


def test_next_monday_on_sunday():
    """"next Monday" on a Sunday resolves to the very next day (2013-02-11).

    Convention: `next_day_of_week` uses ISO weeks; from a Sunday (last day of
    the ISO week), "next Monday" is tomorrow rather than 8 days out.
    """
    value = _parse_time("next Monday", _ctx_en(2013, 2, 10))
    assert value is not None
    assert value["value"].startswith("2013-02-11")
    assert value["grain"] == "day"


# ---------------------------------------------------------------------------
# 7. "Last Monday" on Monday (reference Mon 2013-02-11)


def test_last_monday_on_monday():
    """"last Monday" on a Monday returns the prior week's Monday (2013-02-04)."""
    value = _parse_time("last Monday", _ctx_en(2013, 2, 11))
    assert value is not None
    assert value["value"].startswith("2013-02-04")
    assert value["grain"] == "day"


# ---------------------------------------------------------------------------
# 8. "Today" idempotence (reference 2013-02-12 04:30)


def test_today_idempotence():
    """"today" returns the date of the reference, day-grain, time stripped."""
    value = _parse_time("today", _ctx_en(2013, 2, 12, 4, 30))
    assert value is not None
    assert value["value"] == "2013-02-12T00:00:00+00:00"
    assert value["grain"] == "day"


# ---------------------------------------------------------------------------
# 9. Past clock time — rolls forward to the next day


def test_past_clock_time_rolls_to_next_day():
    """At 18:00, "5pm" already passed — resolver picks next day's 17:00.

    Locks in `_clock_value`'s "future-only" semantics for clock-of-day matches.
    """
    value = _parse_time("5pm", _ctx_en(2013, 2, 12, 18, 0))
    assert value is not None
    assert value["value"] == "2013-02-13T17:00:00+00:00"
    assert value["grain"] == "hour"


# ---------------------------------------------------------------------------
# 10. Future clock time on the same day


def test_future_clock_time_stays_today():
    """At 04:30, "5pm" is later today — resolver picks 17:00 today."""
    value = _parse_time("5pm", _ctx_en(2013, 2, 12, 4, 30))
    assert value is not None
    assert value["value"] == "2013-02-12T17:00:00+00:00"
    assert value["grain"] == "hour"


# ---------------------------------------------------------------------------
# 11. Holiday that has just passed this year (reference 2013-12-26)


def test_holiday_just_passed_resolves_to_next_year():
    """"Christmas" on Dec 26 resolves to *next* year's Christmas, not yesterday.

    `month_day` rolls forward when the candidate is strictly before the
    reference day, so the resolution is 2014-12-25.
    """
    value = _parse_time("Christmas", _ctx_en(2013, 12, 26))
    assert value is not None
    assert value["value"].startswith("2014-12-25")
    assert value["grain"] == "day"
    assert value.get("holiday") == "Christmas"


# ---------------------------------------------------------------------------
# 12. End-of-year rollover for "next year"


def test_next_year_at_year_end():
    """"next year" on 2013-12-31 resolves to start of 2014, year-grain."""
    value = _parse_time("next year", _ctx_en(2013, 12, 31))
    assert value is not None
    assert value["value"] == "2014-01-01T00:00:00+00:00"
    assert value["grain"] == "year"


# ---------------------------------------------------------------------------
# 13. DST-like skip — puckling uses naive UTC, no DST modeling


# TODO(puckling): edge case — puckling does not model DST transitions.
# The resolver works in the reference's tzinfo (UTC in tests), so a phrase
# like "in 1 hour" across a Spring-forward boundary will not skip the missing
# hour. We document the gap rather than mask it with a fake assertion.
@pytest.mark.xfail(
    reason="puckling does not model DST; arithmetic across spring-forward is naive",
    strict=False,
)
def test_dst_spring_forward_skip():
    """A 1-hour shift across a US DST spring-forward should account for the missing hour.

    The assertion below intentionally encodes the DST-aware result a tz-aware
    resolver would produce; the xfail marker flips green once such a resolver
    lands. Remove the mark when DST modeling is added.
    """
    # 2024-03-10 06:30 UTC == 01:30 America/New_York, right before spring-forward.
    ref = dt.datetime(2024, 3, 10, 6, 30, tzinfo=dt.UTC)
    ctx = Context(reference_time=ref, locale=Locale(Lang.EN))
    value = _time_value(parse("in 1 hour", ctx, Options(), dims=("time",)))
    assert value is not None
    # DST-aware expectation: skip the missing 02:00–03:00 EST window, land at
    # 03:30 EDT == 2024-03-10 07:30 UTC + 1h ahead of naive shift = 08:30 UTC.
    assert value["value"] == "2024-03-10T08:30:00+00:00"
