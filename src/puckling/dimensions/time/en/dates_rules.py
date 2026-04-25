"""Supplemental English Time rules — numeric and ordinal dates.

Coverage filled in by this module (the foundation rules already cover
month-and-day-name forms, holidays, weekdays, slash dates with year, etc.):

- ISO-8601 timestamps with `T` separator (e.g. ``2013-02-15T17:30:00``).
- Unambiguous DD/MM/YYYY dates (day > 12, falling outside the existing
  MM/DD/YYYY rule).
- Bare years and "the year <n>" forms.
- "<weekday> the <ordinal-of-month>" combinations (e.g. "monday the 5th").
- "<ordinal> <weekday>" / "the <ordinal> <weekday>" — the n-th occurrence
  of a weekday in the next future occurrence's month.

Anything that does not have a clean compositional path through the existing
helpers is annotated with ``# TODO(puckling): edge case``.
"""

from __future__ import annotations

import dataclasses
import datetime as dt

from puckling.dimensions.time.en._helpers import (
    RelTime,
    fixed_year,
    get_int_value,
    year_month_day,
)
from puckling.dimensions.time.grain import Grain
from puckling.dimensions.time.types import InstantValue
from puckling.predicates import is_ordinal
from puckling.types import RegexMatch, Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Token / value helpers (kept private to this module).


def _tt(value: RelTime) -> Token:
    return Token(dim="time", value=value)


def _is_named_dow(t: Token) -> bool:
    """Match weekday-name time tokens emitted by the foundation rules."""
    if t.dim != "time":
        return False
    rt = t.value
    key = getattr(rt, "key", None)
    return bool(key) and key[0] == "dow_rel"


def _weekday_of(t: Token) -> int | None:
    if not _is_named_dow(t):
        return None
    key = t.value.key
    return key[1] if len(key) > 1 else None


def _is_month_grain(t: Token) -> bool:
    return t.dim == "time" and getattr(t.value, "grain", None) is Grain.MONTH


_ORDINAL_WORDS: dict[str, int] = {
    "first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3,
    "fourth": 4, "4th": 4, "fifth": 5, "5th": 5, "sixth": 6, "6th": 6,
    "seventh": 7, "7th": 7, "eighth": 8, "8th": 8, "ninth": 9, "9th": 9,
    "tenth": 10, "10th": 10, "eleventh": 11, "11th": 11,
    "twelfth": 12, "12th": 12, "thirteenth": 13, "13th": 13,
    "fourteenth": 14, "14th": 14, "fifteenth": 15, "15th": 15,
    "sixteenth": 16, "16th": 16, "seventeenth": 17, "17th": 17,
    "eighteenth": 18, "18th": 18, "nineteenth": 19, "19th": 19,
    "twentieth": 20, "20th": 20, "twenty-first": 21, "21st": 21,
    "twenty-second": 22, "22nd": 22, "twenty-third": 23, "23rd": 23,
    "twenty-fourth": 24, "24th": 24, "twenty-fifth": 25, "25th": 25,
    "twenty-sixth": 26, "26th": 26, "twenty-seventh": 27, "27th": 27,
    "twenty-eighth": 28, "28th": 28, "twenty-ninth": 29, "29th": 29,
    "thirtieth": 30, "30th": 30, "thirty-first": 31, "31st": 31,
}


def _ord_text_to_int(text: str) -> int | None:
    text = text.strip().lower()
    if text in _ORDINAL_WORDS:
        return _ORDINAL_WORDS[text]
    stripped = text.rstrip("stndrh.")
    if stripped.isdigit():
        return int(stripped)
    return None


def _ord_value(t: Token) -> int | None:
    """Extract a small ordinal value from an ordinal token, regex, or numeral."""
    if t.dim == "ordinal":
        v = getattr(t.value, "value", None)
        if isinstance(v, int):
            return v
    if t.dim == "regex_match" and isinstance(t.value, RegexMatch):
        return _ord_text_to_int(t.value.text)
    if t.dim == "numeral":
        v = get_int_value(t.value)
        if v is not None:
            return v
    return None


# ---------------------------------------------------------------------------
# ISO-8601 timestamp with 'T'.


def _iso_timestamp_prod(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[0].value
    if not isinstance(m, RegexMatch):
        return None
    raw_year = m.groups[0] if len(m.groups) > 0 else None
    raw_month = m.groups[1] if len(m.groups) > 1 else None
    raw_day = m.groups[2] if len(m.groups) > 2 else None
    raw_hour = m.groups[3] if len(m.groups) > 3 else None
    raw_minute = m.groups[4] if len(m.groups) > 4 else None
    raw_second = m.groups[5] if len(m.groups) > 5 else None
    if (
        raw_year is None
        or raw_month is None
        or raw_day is None
        or raw_hour is None
        or raw_minute is None
    ):
        return None
    try:
        y = int(raw_year)
        mo = int(raw_month)
        d = int(raw_day)
        h = int(raw_hour)
        mi = int(raw_minute)
        s = int(raw_second) if raw_second is not None else 0
    except (ValueError, IndexError, TypeError):
        return None
    try:
        value = dt.datetime(y, mo, d, h, mi, s, tzinfo=dt.UTC)
    except ValueError:
        return None
    inst = InstantValue(value=value, grain=Grain.SECOND)

    def go(_ref: dt.datetime) -> InstantValue | None:
        return inst

    return _tt(
        RelTime(
            compute=go,
            grain=Grain.SECOND,
            key=("iso_timestamp", value.isoformat()),
        )
    )


# Tolerates an optional fractional seconds and Z/offset suffix without
# committing to timezone arithmetic.
# TODO(puckling): edge case — explicit offsets ("+02:00", "-0500") are
# matched but discarded; we always resolve in UTC.
_ISO_TS_PATTERN = (
    r"(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])"
    r"[Tt ]"
    r"([01]\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?"
    r"(?:\.\d+)?"
    r"(?:Z|[+\-]\d{2}:?\d{2})?"
)

_iso_timestamp_rule = Rule(
    name="iso-8601 timestamp",
    pattern=(regex(_ISO_TS_PATTERN),),
    prod=_iso_timestamp_prod,
)


# ---------------------------------------------------------------------------
# Unambiguous DD/MM/YYYY (only when day > 12 so it cannot collide with the
# foundation MM/DD/YYYY rule).


def _ddmmyyyy_prod(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[0].value
    if not isinstance(m, RegexMatch):
        return None
    groups = [g for g in m.groups if g is not None]
    if len(groups) < 3:
        return None
    try:
        d, mo, y = int(groups[0]), int(groups[1]), int(groups[2])
    except ValueError:
        return None
    if y < 70:
        y += 2000
    elif y < 100:
        y += 1900
    return _tt(year_month_day(y, mo, d))


# day must be 13..31; month 1..12; year 2-4 digits.
_ddmmyyyy_rule = Rule(
    name="dd/mm/yyyy (day > 12)",
    pattern=(
        regex(
            r"(1[3-9]|2\d|3[01])[/\-.](0?[1-9]|1[0-2])[/\-.](\d{2,4})"
        ),
    ),
    prod=_ddmmyyyy_prod,
)


# ---------------------------------------------------------------------------
# Bare years (latent) and "the year <n>".


def _bare_year_prod(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[0].value
    if not isinstance(m, RegexMatch):
        return None
    try:
        y = int(m.text)
    except ValueError:
        return None
    if y < 1000 or y > 9999:
        return None
    # A bare 4-digit number is highly ambiguous, so we mark it latent —
    # callers must opt in via Options(with_latent=True).
    return _tt(dataclasses.replace(fixed_year(y), latent=True, key=("bare_year", y)))


_bare_year_rule = Rule(
    name="<year> (latent 4-digit)",
    pattern=(regex(r"\d{4}"),),
    prod=_bare_year_prod,
)


def _the_year_prod(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[1].value
    if not isinstance(m, RegexMatch):
        return None
    try:
        y = int(m.text)
    except ValueError:
        return None
    if y < 1 or y > 9999:
        return None
    return _tt(fixed_year(y))


_the_year_rule = Rule(
    name="the year <n>",
    pattern=(regex(r"the\s+year"), regex(r"\d{1,4}")),
    prod=_the_year_prod,
)


# ---------------------------------------------------------------------------
# "<weekday> the <ordinal>": "monday the 5th", "tuesday the 22nd".
#
# Resolves to the next future date that is both the named weekday and falls on
# the given day-of-month.


def _dow_the_dom_prod(tokens: tuple[Token, ...]) -> Token | None:
    weekday = _weekday_of(tokens[0])
    n = _ord_value(tokens[2])
    if weekday is None or n is None or not 1 <= n <= 31:
        return None

    def go(ref: dt.datetime) -> InstantValue | None:
        ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
        # ~5 years of slack — calendar dates only repeat (dow, dom) every 28y.
        for offset in range(0, 366 * 5):
            cand = ref_day + dt.timedelta(days=offset)
            if cand.day == n and cand.weekday() == weekday:
                return InstantValue(value=cand, grain=Grain.DAY)
        return None

    return _tt(
        RelTime(compute=go, grain=Grain.DAY, key=("dow_the_dom", weekday, n))
    )


_dow_the_dom_ordinal_rule = Rule(
    name="<dow> the <ordinal>",
    pattern=(
        predicate(_is_named_dow, "is_dow"),
        regex(r"the"),
        predicate(is_ordinal, "is_ordinal"),
    ),
    prod=_dow_the_dom_prod,
)

_DOM_REGEX = (
    r"(?:[12]\d|3[01]|0?[1-9])(?:st|nd|rd|th)?"
    + "|"
    + "|".join(sorted(_ORDINAL_WORDS.keys(), key=len, reverse=True))
)

_dow_the_dom_regex_rule = Rule(
    name="<dow> the <ordinal-regex>",
    pattern=(
        predicate(_is_named_dow, "is_dow"),
        regex(r"the"),
        regex(_DOM_REGEX),
    ),
    prod=_dow_the_dom_prod,
)


# ---------------------------------------------------------------------------
# "<ordinal> <weekday>" / "the <ordinal> <weekday>": "first monday".
#
# Interpretation: the n-th occurrence of that weekday, scanning from the
# reference month forward. So if today is 2013-02-12, "first monday" is
# the first Monday of February 2013 (= 2013-02-04, latent / past) — but
# Duckling's convention is to skip past dates and return the first match in
# the next future month boundary. We follow that: pick the first month
# starting from this month where the n-th weekday occurrence is >= today.


def _ord_dow_prod_inner(weekday: int, n: int) -> RelTime:
    def go(ref: dt.datetime) -> InstantValue | None:
        ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
        year, month = ref_day.year, ref_day.month
        for _ in range(24):  # scan up to two years ahead
            first = dt.datetime(year, month, 1, tzinfo=ref.tzinfo)
            offset = (weekday - first.weekday()) % 7
            day = 1 + offset + 7 * (n - 1)
            try:
                cand = dt.datetime(year, month, day, tzinfo=ref.tzinfo)
            except ValueError:
                cand = None
            if cand is not None and cand >= ref_day:
                return InstantValue(value=cand, grain=Grain.DAY)
            if month == 12:
                year, month = year + 1, 1
            else:
                month += 1
        return None

    return RelTime(
        compute=go,
        grain=Grain.DAY,
        key=("ord_dow", n, weekday),
    )


_ORD_DOW_PATTERN = "|".join(
    sorted(_ORDINAL_WORDS.keys(), key=len, reverse=True)
)


def _ord_dow_prod_at(ord_idx: int, dow_idx: int):
    """Build a production that reads ord at `ord_idx` and dow at `dow_idx`."""

    def prod(tokens: tuple[Token, ...]) -> Token | None:
        n = _ord_value(tokens[ord_idx])
        weekday = _weekday_of(tokens[dow_idx])
        if n is None or weekday is None or not 1 <= n <= 5:
            return None
        return _tt(_ord_dow_prod_inner(weekday, n))

    return prod


_ord_dow_rule = Rule(
    name="<ordinal> <weekday>",
    pattern=(
        predicate(is_ordinal, "is_ordinal"),
        predicate(_is_named_dow, "is_dow"),
    ),
    prod=_ord_dow_prod_at(0, 1),
)

_ord_regex_dow_rule = Rule(
    name="<ordinal-regex> <weekday>",
    pattern=(
        regex(_ORD_DOW_PATTERN),
        predicate(_is_named_dow, "is_dow"),
    ),
    prod=_ord_dow_prod_at(0, 1),
)

_the_ord_dow_rule = Rule(
    name="the <ordinal> <weekday>",
    pattern=(
        regex(r"the"),
        predicate(is_ordinal, "is_ordinal"),
        predicate(_is_named_dow, "is_dow"),
    ),
    prod=_ord_dow_prod_at(1, 2),
)

_the_ord_regex_dow_rule = Rule(
    name="the <ordinal-regex> <weekday>",
    pattern=(
        regex(r"the"),
        regex(_ORD_DOW_PATTERN),
        predicate(_is_named_dow, "is_dow"),
    ),
    prod=_ord_dow_prod_at(1, 2),
)


# ---------------------------------------------------------------------------
# "<ordinal> <weekday> of <named-month>": "first monday of march".


def _ord_dow_of_month_inner(weekday: int, n: int, month_rt: RelTime) -> RelTime:
    def go(ref: dt.datetime) -> InstantValue | None:
        v = month_rt.compute(ref)
        if not isinstance(v, InstantValue):
            return None
        anchor = v.value
        first = dt.datetime(anchor.year, anchor.month, 1, tzinfo=anchor.tzinfo)
        offset = (weekday - first.weekday()) % 7
        day = 1 + offset + 7 * (n - 1)
        try:
            cand = dt.datetime(anchor.year, anchor.month, day, tzinfo=anchor.tzinfo)
        except ValueError:
            return None
        return InstantValue(value=cand, grain=Grain.DAY)

    return RelTime(
        compute=go,
        grain=Grain.DAY,
        key=("ord_dow_of_month", n, weekday, month_rt.key),
    )


def _ord_dow_of_month_prod_at(ord_idx: int, dow_idx: int):
    def prod(tokens: tuple[Token, ...]) -> Token | None:
        n = _ord_value(tokens[ord_idx])
        weekday = _weekday_of(tokens[dow_idx])
        month_tok = tokens[-1]
        if n is None or weekday is None or not 1 <= n <= 5:
            return None
        if not _is_month_grain(month_tok):
            return None
        return _tt(_ord_dow_of_month_inner(weekday, n, month_tok.value))

    return prod


_ord_dow_of_month_rule = Rule(
    name="<ordinal> <weekday> of <month>",
    pattern=(
        predicate(is_ordinal, "is_ordinal"),
        predicate(_is_named_dow, "is_dow"),
        regex(r"of|in"),
        predicate(_is_month_grain, "is_month"),
    ),
    prod=_ord_dow_of_month_prod_at(0, 1),
)

_ord_regex_dow_of_month_rule = Rule(
    name="<ordinal-regex> <weekday> of <month>",
    pattern=(
        regex(_ORD_DOW_PATTERN),
        predicate(_is_named_dow, "is_dow"),
        regex(r"of|in"),
        predicate(_is_month_grain, "is_month"),
    ),
    prod=_ord_dow_of_month_prod_at(0, 1),
)


_the_ord_dow_of_month_rule = Rule(
    name="the <ordinal> <weekday> of <month>",
    pattern=(
        regex(r"the"),
        predicate(is_ordinal, "is_ordinal"),
        predicate(_is_named_dow, "is_dow"),
        regex(r"of|in"),
        predicate(_is_month_grain, "is_month"),
    ),
    prod=_ord_dow_of_month_prod_at(1, 2),
)


# ---------------------------------------------------------------------------
# Aggregate.


RULES: tuple[Rule, ...] = (
    _iso_timestamp_rule,
    _ddmmyyyy_rule,
    _bare_year_rule,
    _the_year_rule,
    _dow_the_dom_ordinal_rule,
    _dow_the_dom_regex_rule,
    _ord_dow_rule,
    _ord_regex_dow_rule,
    _the_ord_dow_rule,
    _the_ord_regex_dow_rule,
    _ord_dow_of_month_rule,
    _ord_regex_dow_of_month_rule,
    _the_ord_dow_of_month_rule,
)
