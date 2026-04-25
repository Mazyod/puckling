"""Supplemental English Time rules — additional holidays and seasons.

Foundation already provides Time EN rules covering Christmas, Easter, Halloween,
New Year, Valentine's Day, Thanksgiving, MLK Day, Black Friday, Mother's Day,
Father's Day, and Labor Day. This module fills the remaining gaps from
Duckling's `Duckling/Time/EN/Rules.hs`:

- Memorial Day (last Monday of May)
- Columbus Day (2nd Monday of October)
- Canadian Thanksgiving (2nd Monday of October)
- Cinco de Mayo, Juneteenth, Veterans Day, Presidents' Day
- Seasons: spring, summer, fall, autumn, winter (Northern Hemisphere intervals)
- Year-relative holidays: "Easter 2015", "Christmas 2015", etc.

Hard / context-sensitive cases that depend on Duckling's richer combinator
algebra (multi-day religious spans like Hanukkah / Ramadan, lunar Chinese New
Year, regional Southern-hemisphere season inversion) are flagged with
`# TODO(puckling): edge case`.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable

from puckling.dimensions.time.en._helpers import (
    RelTime,
    from_time_data,
    month_day,
)
from puckling.dimensions.time.grain import Grain
from puckling.dimensions.time.holiday_helpers import computed_holiday
from puckling.dimensions.time.types import (
    InstantValue,
    IntervalValue,
)
from puckling.types import RegexMatch, Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Helpers


def _tt(value: RelTime) -> Token:
    return Token(dim="time", value=value)


# ---------------------------------------------------------------------------
# Computed-date helpers (year -> dt.date)


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> dt.date:
    """The `n`-th occurrence of `weekday` (Mon=0..Sun=6) in `month`."""
    first = dt.date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + dt.timedelta(days=offset + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> dt.date:
    """The last `weekday` in `month` of `year`."""
    # Day 28 always exists; walk forward to find candidate, then back 7 if past.
    next_month_first = (
        dt.date(year + 1, 1, 1) if month == 12 else dt.date(year, month + 1, 1)
    )
    last = next_month_first - dt.timedelta(days=1)
    offset = (last.weekday() - weekday) % 7
    return last - dt.timedelta(days=offset)


def thanksgiving_us(year: int) -> dt.date:
    """US Thanksgiving — 4th Thursday of November."""
    return _nth_weekday(year, 11, 3, 4)


def thanksgiving_canada(year: int) -> dt.date:
    """Canadian Thanksgiving — 2nd Monday of October."""
    return _nth_weekday(year, 10, 0, 2)


def memorial_day(year: int) -> dt.date:
    """Memorial Day — last Monday of May."""
    return _last_weekday(year, 5, 0)


def columbus_day(year: int) -> dt.date:
    """Columbus Day — 2nd Monday of October."""
    return _nth_weekday(year, 10, 0, 2)


def mlk_day(year: int) -> dt.date:
    """Martin Luther King Jr. Day — 3rd Monday of January."""
    return _nth_weekday(year, 1, 0, 3)


def labor_day_us(year: int) -> dt.date:
    """US Labor Day — 1st Monday of September."""
    return _nth_weekday(year, 9, 0, 1)


def mothers_day(year: int) -> dt.date:
    """Mother's Day — 2nd Sunday of May."""
    return _nth_weekday(year, 5, 6, 2)


def fathers_day(year: int) -> dt.date:
    """Father's Day — 3rd Sunday of June."""
    return _nth_weekday(year, 6, 6, 3)


def black_friday(year: int) -> dt.date:
    """Black Friday — Friday after US Thanksgiving."""
    return thanksgiving_us(year) + dt.timedelta(days=1)


def presidents_day(year: int) -> dt.date:
    """Presidents' Day — 3rd Monday of February."""
    return _nth_weekday(year, 2, 0, 3)


def veterans_day(year: int) -> dt.date:
    """Veterans Day — November 11."""
    return dt.date(year, 11, 11)


# ---------------------------------------------------------------------------
# Computed holiday rule builder


def _computed_holiday_rule(
    name: str,
    pat: str,
    date_for: Callable[[int], dt.date],
) -> Rule:
    """Build a rule resolving via foundation's `computed_holiday(name, date_for)`."""
    td = computed_holiday(name, date_for)
    rt = from_time_data(td)

    def prod(_: tuple[Token, ...]) -> Token | None:
        return _tt(rt)

    return Rule(name=f"holiday: {name}", pattern=(regex(pat),), prod=prod)


# ---------------------------------------------------------------------------
# Fixed-date supplemental holidays


def _fixed_holiday_rule(name: str, pat: str, month: int, day: int) -> Rule:
    def prod(_: tuple[Token, ...]) -> Token | None:
        return _tt(month_day(month, day, holiday=name))

    return Rule(name=f"holiday: {name}", pattern=(regex(pat),), prod=prod)


_FIXED_SUPPLEMENTAL = (
    ("Cinco de Mayo", r"cinco de mayo", 5, 5),
    ("Juneteenth", r"juneteenth(\s+(national\s+)?independence(\s+day)?)?", 6, 19),
    ("Veterans Day", r"veteran'?s?\s+day|veterans'\s+day|armistice\s+day", 11, 11),
    ("Flag Day", r"flag\s+day", 6, 14),
    ("Groundhog Day", r"groundhog'?s?\s+day", 2, 2),
    ("Patriot Day", r"patriot'?s?\s+day", 9, 11),
    ("Bastille Day", r"bastille\s+day", 7, 14),
    ("Canada Day", r"canada\s+day", 7, 1),
    ("Boxing Day", r"boxing day|st\.?\s+stephen'?s\s+day", 12, 26),
    ("Guy Fawkes Day", r"guy\s+fawkes(\s+(day|night))?|bonfire\s+night", 11, 5),
    ("Remembrance Day", r"remembrance\s+day|poppy\s+day", 11, 11),
)


# ---------------------------------------------------------------------------
# Seasons (Northern Hemisphere; intervals)


def _season(name: str, start: tuple[int, int], end: tuple[int, int]) -> RelTime:
    """Season as a yearly interval [start, end). `start`/`end` are (month, day)."""
    sm, sd = start
    em, ed = end

    def go(ref: dt.datetime) -> IntervalValue | None:
        # Find the next year whose season window has not yet fully passed.
        # If the start is later in the calendar than the end (winter),
        # the interval crosses the year boundary.
        ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
        for year_offset in (0, 1):
            base_year = ref.year + year_offset
            try:
                start_dt = dt.datetime(base_year, sm, sd, tzinfo=ref.tzinfo)
                if (em, ed) <= (sm, sd):
                    end_dt = dt.datetime(base_year + 1, em, ed, tzinfo=ref.tzinfo)
                else:
                    end_dt = dt.datetime(base_year, em, ed, tzinfo=ref.tzinfo)
            except ValueError:
                continue
            if end_dt >= ref_day:
                return IntervalValue(
                    start=InstantValue(value=start_dt, grain=Grain.DAY),
                    end=InstantValue(value=end_dt, grain=Grain.DAY),
                )
        return None

    return RelTime(
        compute=go,
        grain=Grain.DAY,
        holiday=name,
        key=("season", name),
    )


def _season_rule(name: str, pat: str, start: tuple[int, int], end: tuple[int, int]) -> Rule:
    rt = _season(name, start, end)

    def prod(_: tuple[Token, ...]) -> Token | None:
        return _tt(rt)

    return Rule(name=f"season: {name}", pattern=(regex(pat),), prod=prod)


_SEASONS: tuple[Rule, ...] = (
    # TODO(puckling): edge case — Southern-hemisphere locales invert these.
    _season_rule("summer", r"summer", (6, 21), (9, 23)),
    _season_rule("fall", r"fall|autumn", (9, 23), (12, 21)),
    _season_rule("winter", r"winter", (12, 21), (3, 20)),
    _season_rule("spring", r"spring", (3, 20), (6, 21)),
)


# ---------------------------------------------------------------------------
# Year-relative holidays — "Easter 2015", "Christmas 2015"


def _is_holiday_time(t: Token) -> bool:
    if t.dim != "time":
        return False
    return getattr(t.value, "holiday", None) is not None


def _resolve_holiday_in_year(rt: RelTime, year: int) -> RelTime:
    """Resolve `rt` as if the reference were Jan 1 of `year`.

    Holiday closures search forward from the reference, so anchoring the
    reference to Jan 1 of the target year yields that year's occurrence —
    even for computed holidays like Easter where a simple year-replace on a
    pre-resolved date would be wrong (Easter falls on different days each
    year).
    """

    def go(ref: dt.datetime) -> InstantValue | IntervalValue | None:
        synthetic_ref = dt.datetime(year, 1, 1, tzinfo=ref.tzinfo)
        v = rt.compute(synthetic_ref)
        if isinstance(v, InstantValue) and v.value.year != year:
            try:
                return InstantValue(value=v.value.replace(year=year), grain=v.grain)
            except ValueError:
                return None
        return v

    return RelTime(
        compute=go,
        grain=rt.grain,
        holiday=rt.holiday,
        key=("holiday_in_year", rt.key, year),
    )


def _make_holiday_year_prod(year_idx: int) -> Callable[[tuple[Token, ...]], Token | None]:
    def prod(tokens: tuple[Token, ...]) -> Token | None:
        holiday_tok = tokens[0]
        year_tok = tokens[year_idx]
        if not isinstance(year_tok.value, RegexMatch):
            return None
        try:
            y = int(year_tok.value.text)
        except ValueError:
            return None
        if y < 100:
            y += 2000
        rt: RelTime = holiday_tok.value
        return _tt(_resolve_holiday_in_year(rt, y))

    return prod


_holiday_year_rule = Rule(
    name="<holiday> <year>",
    pattern=(
        predicate(_is_holiday_time, "is_holiday"),
        regex(r"\d{4}"),
    ),
    prod=_make_holiday_year_prod(1),
)

_holiday_in_year_rule = Rule(
    name="<holiday> in <year>",
    pattern=(
        predicate(_is_holiday_time, "is_holiday"),
        regex(r"in|of"),
        regex(r"\d{4}"),
    ),
    prod=_make_holiday_year_prod(2),
)


# ---------------------------------------------------------------------------
# "the day before/after <holiday>" — useful spans like Christmas Eve variants
# Foundation already covers most named eves; we add a generic before/after day
# absorber for any holiday-bearing time token.


def _eve_or_day_after_prod(
    tokens: tuple[Token, ...],
) -> Token | None:
    direction_tok = tokens[0]
    holiday_tok = tokens[-1]
    if not isinstance(direction_tok.value, RegexMatch):
        return None
    text = direction_tok.value.text.lower()
    days = -1 if "before" in text else 1
    rt: RelTime = holiday_tok.value
    holiday_name = rt.holiday

    def go(ref: dt.datetime) -> InstantValue | None:
        v = rt.compute(ref)
        if not isinstance(v, InstantValue):
            return None
        new_value = v.value + dt.timedelta(days=days)
        return InstantValue(value=new_value, grain=Grain.DAY)

    return _tt(
        RelTime(
            compute=go,
            grain=Grain.DAY,
            holiday=holiday_name,
            key=("eve_or_day_after", rt.key, days),
        )
    )


_day_before_holiday_rule = Rule(
    name="the day before <holiday>",
    pattern=(
        regex(r"(the\s+)?day\s+before"),
        predicate(_is_holiday_time, "is_holiday"),
    ),
    prod=_eve_or_day_after_prod,
)

_day_after_holiday_rule = Rule(
    name="the day after <holiday>",
    pattern=(
        regex(r"(the\s+)?day\s+after"),
        predicate(_is_holiday_time, "is_holiday"),
    ),
    prod=_eve_or_day_after_prod,
)


# ---------------------------------------------------------------------------
# Aggregate

_FIXED_RULES: tuple[Rule, ...] = tuple(
    _fixed_holiday_rule(n, p, m, d) for n, p, m, d in _FIXED_SUPPLEMENTAL
)

_COMPUTED_RULES: tuple[Rule, ...] = (
    _computed_holiday_rule("Memorial Day", r"memorial\s+day", memorial_day),
    _computed_holiday_rule("Columbus Day", r"columbus\s+day", columbus_day),
    _computed_holiday_rule(
        "Canadian Thanksgiving",
        r"canadian\s+thanksgiving(\s+day)?|thanksgiving\s+(day\s+)?in\s+canada",
        thanksgiving_canada,
    ),
    _computed_holiday_rule(
        "Presidents' Day",
        r"presidents?'?\s+day|washington'?s?\s+birthday",
        presidents_day,
    ),
)


RULES: tuple[Rule, ...] = (
    *_FIXED_RULES,
    *_COMPUTED_RULES,
    *_SEASONS,
    _holiday_year_rule,
    _holiday_in_year_rule,
    _day_before_holiday_rule,
    _day_after_holiday_rule,
)
