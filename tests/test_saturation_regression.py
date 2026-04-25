"""Saturation / performance regression tests for the puckling engine.

The saturating fixed-point parser can produce exponential token growth on
certain compositionally-rich inputs. We lock in which phrases must complete
quickly so that engine refactors that regress this property fail loudly.

Each test caps wall-clock runtime via ``@pytest.mark.timeout(N)``; any
regression that pushes a previously-fast phrase past the bound will fail the
suite. Known-bad phrases (which currently saturate) are marked ``xfail`` so
that, if/when the engine is fixed, the unexpected pass alerts us.
"""

from __future__ import annotations

import pytest

from puckling import Entity, Options, parse


def _intervals(entities: list[Entity]) -> list[Entity]:
    return [e for e in entities if isinstance(e.value, dict) and e.value.get("type") == "interval"]


# Category 1: known-pathological phrases must complete within a tight bound.


@pytest.mark.timeout(2)
def test_third_monday_of_october_2014(ctx_en):
    parse("the third Monday of October 2014", ctx_en, Options())


@pytest.mark.timeout(2)
def test_between_march_1_and_march_5(ctx_en):
    parse("between March 1 and March 5", ctx_en, Options())


@pytest.mark.timeout(2)
def test_from_5pm_to_7pm_tomorrow(ctx_en):
    parse("from 5pm to 7pm tomorrow", ctx_en, Options())


@pytest.mark.timeout(2)
def test_in_3_weeks_and_2_days(ctx_en):
    parse("in 3 weeks and 2 days", ctx_en, Options())


@pytest.mark.timeout(2)
def test_long_compound_completes_quickly(ctx_en):
    """Mixed-dimension compound (email, time, money, phone, distance)."""
    parse("alice@example.com tomorrow at 5pm $50 (415) 555-1212 5km", ctx_en, Options())


@pytest.mark.timeout(2)
def test_arabic_between_friday_and_monday(ctx_ar):
    parse("بين الجمعة و الاثنين", ctx_ar, Options())


@pytest.mark.timeout(2)
def test_arabic_from_tomorrow_to_friday(ctx_ar):
    parse("من غدا الى الجمعة", ctx_ar, Options())


@pytest.mark.timeout(2)
def test_arabic_five_pm(ctx_ar):
    parse("الساعة الخامسة مساء", ctx_ar, Options())


@pytest.mark.timeout(2)
def test_arabic_fifty_kuwaiti_dinar(ctx_ar):
    parse("٥٠ دينار كويتي", ctx_ar, Options())


# Category 2: stress — 100 numerals in a row.


@pytest.mark.timeout(2)
def test_one_hundred_numerals_in_a_row(ctx_en):
    parse(" ".join(str(i) for i in range(1, 101)), ctx_en, Options())


# Category 3: stress — nested compound time phrase.


@pytest.mark.timeout(2)
def test_nested_compound_day_after_third_monday(ctx_en):
    parse("the day after the third Monday of October in 2024", ctx_en, Options())


# Category 4: per-call state must not accumulate across repeated identical parses.


@pytest.mark.timeout(2)
def test_repeated_calls_dont_accumulate_state(ctx_en):
    for _ in range(50):
        parse("tomorrow at 5pm", ctx_en, Options())


@pytest.mark.timeout(2)
def test_repeated_arabic_calls_dont_accumulate_state(ctx_ar):
    for _ in range(50):
        parse("الساعة الخامسة مساء", ctx_ar, Options())


# Category 5: previously-saturating Arabic interval phrases. With the engine's
# `parse_timeout_ms` budget (default 2 s), the parser bails partway through
# saturation and surfaces an interval entity from the partial token forest.
# These tests lock that behavior in: a regression in the budget enforcement
# would re-introduce the hang.


@pytest.mark.timeout(3)
def test_arabic_min_date_ila_date_completes_with_budget(ctx_ar):
    out = parse("من 4 ابريل الى 10 ابريل", ctx_ar, Options(), dims=("time",))
    assert _intervals(out), "engine budget should still surface an interval"


@pytest.mark.timeout(3)
def test_arabic_date_dash_date_completes_with_budget(ctx_ar):
    out = parse("4 ابريل - 10 ابريل", ctx_ar, Options(), dims=("time",))
    assert _intervals(out), "engine budget should still surface an interval"
