"""English Time rules — port of Duckling's `Duckling/Time/EN/Rules.hs`.

Coverage:
- Today / yesterday / tomorrow / now / day-after-tomorrow / day-before-yesterday
- Weekday names (Monday .. Sunday) including next/last/this <weekday>
- Month names (January .. December) including next/last <month>
- Date forms: "<month> <day>", "<day> of <month>", "<day> <month>",
  "<month> <day> <year>", "yyyy-mm-dd", "mm/dd/yyyy", "mm/yyyy", "yyyy/mm"
- Years: "in 2014", AD/BC suffix, year as latent integer
- Clock times: "<H>:<M>", "<H>:<M>:<S>", "<H> o'clock", "<H>am/pm",
  "half past <H>", "quarter past/to <H>", "<H> past <H>", "noon", "midnight"
- Cycles: "this/last/next week/month/year/quarter"
- Relative: "in <duration>", "<duration> ago", "<n> days from now"
- Parts of day: "morning", "afternoon", "evening", "night", "tonight"
- Intervals via "between X and Y", "from X to Y", dash separators
- Holidays: Christmas, New Year's, Halloween, Valentine's, Easter, MLK Day, etc.

Hard / context-sensitive cases that depend on Duckling's richer
combinator algebra (e.g. "the closest <day> to <time>", complex week-of-month
computations, full timezone handling) are marked `# TODO(puckling): edge case`.
"""

from __future__ import annotations

import datetime as dt

from puckling.dimensions.time.computed import easter, orthodox_easter
from puckling.dimensions.time.en._helpers import (
    RelTime,
    at_year_in,
    cycle_nth,
    day_of_week_relative,
    fixed_year,
    get_int_value,
    hour_minute_second_value,
    hour_minute_value,
    hour_value,
    interval,
    last_day_of_week,
    month_day,
    named_month,
    next_day_of_week,
    now,
    open_interval,
    relative_day_offset,
    shift_minutes,
    with_day_of_month,
    year_month,
    year_month_day,
)
from puckling.dimensions.time.grain import Grain, add_grain
from puckling.dimensions.time.types import (
    InstantValue,
    IntervalDirection,
    IntervalValue,
)
from puckling.predicates import is_numeral, is_ordinal, is_time
from puckling.types import RegexMatch, Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Internal helpers


def _tt(value: RelTime) -> Token:
    return Token(dim="time", value=value)


def _value_grain(t: Token) -> Grain | None:
    return getattr(t.value, "grain", None)


def _is_day_grain(t: Token) -> bool:
    return t.dim == "time" and _value_grain(t) is Grain.DAY


def _is_month_grain(t: Token) -> bool:
    return t.dim == "time" and _value_grain(t) is Grain.MONTH


def _is_year_grain(t: Token) -> bool:
    return t.dim == "time" and _value_grain(t) is Grain.YEAR


def _is_hour_or_minute(t: Token) -> bool:
    return t.dim == "time" and _value_grain(t) in (Grain.HOUR, Grain.MINUTE)


def _natural_int(t: Token) -> int | None:
    if not is_numeral(t):
        return None
    return get_int_value(t.value)


# ---------------------------------------------------------------------------
# Word maps


WEEKDAYS = (
    ("Monday", r"mondays?|mon\.?", 0),
    ("Tuesday", r"tuesdays?|tues?\.?", 1),
    ("Wednesday", r"wed?nesdays?|wed\.?", 2),
    ("Thursday", r"thursdays?|thu(rs?)?\.?", 3),
    ("Friday", r"fridays?|fri\.?", 4),
    ("Saturday", r"saturdays?|sat\.?", 5),
    ("Sunday", r"sundays?|sun\.?", 6),
)

MONTHS = (
    ("January", r"january|jan\.?", 1),
    ("February", r"february|feb\.?", 2),
    ("March", r"march|mar\.?", 3),
    ("April", r"april|apr\.?", 4),
    ("May", r"may", 5),
    ("June", r"june|jun\.?", 6),
    ("July", r"july|jul\.?", 7),
    ("August", r"august|aug\.?", 8),
    ("September", r"september|sept?\.?", 9),
    ("October", r"october|oct\.?", 10),
    ("November", r"november|nov\.?", 11),
    ("December", r"december|dec\.?", 12),
)

# Cardinal word -> integer for small numbers commonly written out (1..31).
WORD_NUMS: dict[str, int] = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30,
}

ORDINAL_WORDS: dict[str, int] = {
    "first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3,
    "fourth": 4, "4th": 4, "fifth": 5, "5th": 5, "sixth": 6, "6th": 6,
    "seventh": 7, "7th": 7, "eighth": 8, "8th": 8, "ninth": 9, "9th": 9,
    "tenth": 10, "10th": 10, "eleventh": 11, "11th": 11,
    "twelfth": 12, "12th": 12, "thirteenth": 13, "13th": 13,
    "fourteenth": 14, "14th": 14, "fifteenth": 15, "15th": 15,
    "sixteenth": 16, "16th": 16, "seventeenth": 17, "17th": 17,
    "eighteenth": 18, "18th": 18, "nineteenth": 19, "19th": 19,
    "twentieth": 20, "20th": 20,
    "twenty-first": 21, "21st": 21, "twenty-second": 22, "22nd": 22,
    "twenty-third": 23, "23rd": 23, "twenty-fourth": 24, "24th": 24,
    "twenty-fifth": 25, "25th": 25, "twenty-sixth": 26, "26th": 26,
    "twenty-seventh": 27, "27th": 27, "twenty-eighth": 28, "28th": 28,
    "twenty-ninth": 29, "29th": 29, "thirtieth": 30, "30th": 30,
    "thirty-first": 31, "31st": 31,
}


# ---------------------------------------------------------------------------
# Production helpers shared by rule families


def _instants_rules() -> tuple[Rule, ...]:
    out: list[Rule] = []

    def make(name: str, pat: str, days: int) -> Rule:
        def prod(_: tuple[Token, ...]) -> Token | None:
            return _tt(relative_day_offset(days))

        return Rule(name=name, pattern=(regex(pat),), prod=prod)

    out.append(make("today", r"todays?|(at this time)", 0))
    out.append(make("tomorrow", r"tmrw?|tomm?or?rows?", 1))
    out.append(make("yesterday", r"yesterdays?", -1))
    out.append(make("day after tomorrow", r"the day after tomorrow|day after tomorrow", 2))
    out.append(make("day before yesterday", r"the day before yesterday|day before yesterday", -2))

    def now_prod(_: tuple[Token, ...]) -> Token | None:
        return _tt(now())

    out.append(
        Rule(
            name="now",
            pattern=(regex(r"(just\s*)?now|right\s+now|at\s+the\s+moment|atm|immediately"),),
            prod=now_prod,
        )
    )

    return tuple(out)


def _weekday_rule(name: str, pat: str, weekday: int) -> Rule:
    def prod(_: tuple[Token, ...]) -> Token | None:
        return _tt(day_of_week_relative(weekday))

    return Rule(name=f"day-of-week ({name})", pattern=(regex(pat),), prod=prod)


def _month_rule(name: str, pat: str, month: int) -> Rule:
    def prod(_: tuple[Token, ...]) -> Token | None:
        return _tt(named_month(month))

    return Rule(name=f"month ({name})", pattern=(regex(pat),), prod=prod)


def _all_named_rules() -> tuple[Rule, ...]:
    rules: list[Rule] = []
    for name, pat, wd in WEEKDAYS:
        rules.append(_weekday_rule(name, pat, wd))
    for name, pat, m in MONTHS:
        rules.append(_month_rule(name, pat, m))
    return tuple(rules)


# ---------------------------------------------------------------------------
# Year / month / date


def _year_in_prod(tokens: tuple[Token, ...]) -> Token | None:
    # "in <year>"
    match = tokens[1].value
    text = match.text if isinstance(match, RegexMatch) else None
    if text is None:
        return None
    try:
        y = int(text)
    except ValueError:
        return None
    return _tt(fixed_year(y))


_year_in_rule = Rule(
    name="in <year>",
    pattern=(regex(r"in"), regex(r"\d{2,4}")),
    prod=_year_in_prod,
)


def _year_ad_bc_prod(tokens: tuple[Token, ...]) -> Token | None:
    num_tok = tokens[0]
    suffix = tokens[1].value
    n = _natural_int(num_tok)
    if n is None or n < 1 or n > 10000:
        return None
    if not isinstance(suffix, RegexMatch):
        return None
    text = suffix.text.lower()
    if text.startswith("b"):
        n = -n
    return _tt(fixed_year(n))


_year_adbc_rule = Rule(
    name="<year> AD/BC",
    pattern=(predicate(is_numeral, "is_numeral"), regex(r"a\.?d\.?|b\.?c\.?")),
    prod=_year_ad_bc_prod,
)


def _year_after_in_prod(tokens: tuple[Token, ...]) -> Token | None:
    # "in <year> A.D./AD" form: "in" followed by a number and an a.d./b.c. tag.
    num_match = tokens[1].value
    suffix = tokens[2].value
    if not isinstance(num_match, RegexMatch) or not isinstance(suffix, RegexMatch):
        return None
    try:
        y = int(num_match.text)
    except ValueError:
        return None
    text = suffix.text.lower()
    if text.startswith("b"):
        y = -y
    return _tt(fixed_year(y))


_year_in_adbc_rule = Rule(
    name="in <year> A.D./BC",
    pattern=(regex(r"in"), regex(r"\d{1,4}"), regex(r"a\.?d\.?|b\.?c\.?")),
    prod=_year_after_in_prod,
)


# yyyy-mm-dd
def _yyyymmdd_prod(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[0].value
    if not isinstance(m, RegexMatch):
        return None
    try:
        y, mo, d = (int(g) if g else 0 for g in m.groups[:3])
    except ValueError:
        return None
    if y < 100:  # 2-digit year — assume 20xx
        y += 2000
    return _tt(year_month_day(y, mo, d))


_yyyymmdd_rule = Rule(
    name="yyyy-mm-dd",
    pattern=(regex(r"(\d{2,4})-(0?[1-9]|1[0-2])-(3[01]|[12]\d|0?[1-9])"),),
    prod=_yyyymmdd_prod,
)


# mm/dd/yyyy or mm-dd-yy
def _mm_dd_yyyy_prod(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[0].value
    if not isinstance(m, RegexMatch):
        return None
    groups = [g for g in m.groups if g is not None]
    if len(groups) < 3:
        return None
    try:
        mo, d, y = int(groups[0]), int(groups[1]), int(groups[2])
    except ValueError:
        return None
    if y < 70:
        y += 2000
    elif y < 100:
        y += 1900
    return _tt(year_month_day(y, mo, d))


_mm_dd_yyyy_rule = Rule(
    name="mm/dd/yyyy",
    pattern=(regex(r"(0?[1-9]|1[0-2])[/\-.](3[01]|[12]\d|0?[1-9])[/\-.](\d{2,4})"),),
    prod=_mm_dd_yyyy_prod,
)


# mm/dd (no year)
def _mm_dd_prod(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[0].value
    if not isinstance(m, RegexMatch):
        return None
    groups = [g for g in m.groups if g is not None]
    if len(groups) < 2:
        return None
    try:
        mo, d = int(groups[0]), int(groups[1])
    except ValueError:
        return None
    return _tt(month_day(mo, d))


_mm_dd_rule = Rule(
    name="mm/dd",
    pattern=(regex(r"(0?[1-9]|1[0-2])\s*[/\-]\s*(3[01]|[12]\d|0?[1-9])(?!\d|\s*[/\-]\s*\d)"),),
    prod=_mm_dd_prod,
)


# mm/yyyy
def _mm_yyyy_prod(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[0].value
    if not isinstance(m, RegexMatch):
        return None
    groups = [g for g in m.groups if g is not None]
    if len(groups) < 2:
        return None
    try:
        mo, y = int(groups[0]), int(groups[1])
    except ValueError:
        return None
    return _tt(year_month(y, mo))


_mm_yyyy_rule = Rule(
    name="mm/yyyy",
    pattern=(regex(r"(0?[1-9]|1[0-2])[/\-](\d{4})"),),
    prod=_mm_yyyy_prod,
)


# yyyy/mm
def _yyyy_mm_prod(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[0].value
    if not isinstance(m, RegexMatch):
        return None
    groups = [g for g in m.groups if g is not None]
    if len(groups) < 2:
        return None
    try:
        y, mo = int(groups[0]), int(groups[1])
    except ValueError:
        return None
    return _tt(year_month(y, mo))


_yyyy_mm_rule = Rule(
    name="yyyy/mm",
    pattern=(regex(r"(\d{4})\s*[/\-]\s*(1[0-2]|0?[1-9])"),),
    prod=_yyyy_mm_prod,
)


def _month_year_prod(tokens: tuple[Token, ...]) -> Token | None:
    """e.g. 'October 2014' — a year-anchored named month."""
    month_tok = tokens[0]
    year_match = tokens[1].value
    if not _is_month_grain(month_tok) or not isinstance(year_match, RegexMatch):
        return None
    try:
        y = int(year_match.text)
    except ValueError:
        return None
    if y < 100:
        y += 2000
    return _tt(at_year_in(month_tok.value, y))


_month_year_rule = Rule(
    name="<month> <year>",
    pattern=(predicate(is_time, "is_month"), regex(r"\d{4}")),
    prod=_month_year_prod,
)


# ---------------------------------------------------------------------------
# Day-of-month rules ("the 5th", "5th of march", "march 5")


def _dom_from_token(t: Token) -> int | None:
    """Extract a 1..31 day-of-month value from a numeral or ordinal token."""
    if t.dim == "ordinal":
        v = getattr(t.value, "value", None)
        if isinstance(v, int) and 1 <= v <= 31:
            return v
    if t.dim == "numeral":
        v = get_int_value(t.value)
        if v is not None and 1 <= v <= 31:
            return v
    if t.dim == "regex_match":
        # Ordinal-style regex for "1st", "5th" etc.
        text = t.value.text.lower() if isinstance(t.value, RegexMatch) else ""
        if text in ORDINAL_WORDS:
            return ORDINAL_WORDS[text]
        # bare digits
        try:
            v = int(text.rstrip("stndrh.").rstrip("."))
        except ValueError:
            return None
        if 1 <= v <= 31:
            return v
    return None


# Match "the <ord>" style standalone day-of-month — yields a latent day token.
def _the_dom_prod(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[1].value
    if not isinstance(m, RegexMatch):
        return None
    text = m.text.lower()
    n: int | None
    if text in ORDINAL_WORDS:
        n = ORDINAL_WORDS[text]
    else:
        try:
            n = int(text.rstrip("stndrh."))
        except ValueError:
            n = None
    if n is None or not 1 <= n <= 31:
        return None

    # Build a day-of-month picker that finds the next matching day.
    def go(ref):
        ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
        if ref_day.day <= n:
            try:
                return InstantValue(value=ref_day.replace(day=n), grain=Grain.DAY)
            except ValueError:
                pass
        year = ref_day.year + (1 if ref_day.month == 12 else 0)
        month = 1 if ref_day.month == 12 else ref_day.month + 1
        try:
            cand = dt.datetime(year, month, n, tzinfo=ref.tzinfo)
            return InstantValue(value=cand, grain=Grain.DAY)
        except ValueError:
            return None

    return _tt(RelTime(compute=go, grain=Grain.DAY, latent=True, key=("the_dom", n)))


_the_dom_rule = Rule(
    name="the <day-of-month>",
    pattern=(regex(r"(on\s+)?the"), regex(r"\d{1,2}(?:st|nd|rd|th)?")),
    prod=_the_dom_prod,
)


# Production for "<month> <day>" or "<month> <day-as-ordinal>"
def _month_dom_prod(tokens: tuple[Token, ...]) -> Token | None:
    month_tok, dom_tok = tokens
    if not _is_month_grain(month_tok):
        return None
    n = _dom_from_token(dom_tok)
    if n is None:
        return None
    return _tt(with_day_of_month(month_tok.value, n))


_month_dom_numeric_rule = Rule(
    name="<month> <dom> (number)",
    pattern=(predicate(is_time, "is_month"), predicate(is_numeral, "is_dom_int")),
    prod=_month_dom_prod,
)

_month_dom_ordinal_rule = Rule(
    name="<month> <dom> (ordinal)",
    pattern=(predicate(is_time, "is_month"), predicate(is_ordinal, "is_dom_ord")),
    prod=_month_dom_prod,
)


def _month_dom_regex_prod(tokens: tuple[Token, ...]) -> Token | None:
    month_tok, dom_tok = tokens
    if not _is_month_grain(month_tok):
        return None
    n = _dom_from_token(dom_tok)
    if n is None:
        return None
    return _tt(with_day_of_month(month_tok.value, n))


_month_dom_regex_rule = Rule(
    name="<month> <dom> (regex)",
    pattern=(
        predicate(is_time, "is_month"),
        regex(r"(?:[12]\d|3[01]|0?[1-9])(?:st|nd|rd|th)?"),
    ),
    prod=_month_dom_regex_prod,
)


# "<dom> of <month>" / "<dom> <month>"
def _dom_of_month_prod(tokens: tuple[Token, ...]) -> Token | None:
    dom_tok = tokens[0]
    month_tok = tokens[-1]
    if not _is_month_grain(month_tok):
        return None
    n = _dom_from_token(dom_tok)
    if n is None:
        return None
    return _tt(with_day_of_month(month_tok.value, n))


_dom_of_month_numeral_rule = Rule(
    name="<dom> of <month> (numeral)",
    pattern=(
        predicate(is_numeral, "is_numeral"),
        regex(r"of|in"),
        predicate(is_time, "is_month"),
    ),
    prod=_dom_of_month_prod,
)

_dom_of_month_ordinal_rule = Rule(
    name="<dom> of <month> (ordinal)",
    pattern=(
        predicate(is_ordinal, "is_ordinal"),
        regex(r"of|in"),
        predicate(is_time, "is_month"),
    ),
    prod=_dom_of_month_prod,
)


def _the_dom_of_month_prod(tokens: tuple[Token, ...]) -> Token | None:
    # "the <dom> of <month>"
    dom_tok = tokens[1]
    month_tok = tokens[-1]
    if not _is_month_grain(month_tok):
        return None
    n = _dom_from_token(dom_tok)
    if n is None:
        return None
    return _tt(with_day_of_month(month_tok.value, n))


_the_dom_of_month_ord_rule = Rule(
    name="the <dom> of <month> (ordinal)",
    pattern=(
        regex(r"the"),
        predicate(is_ordinal, "is_ordinal"),
        regex(r"of|in"),
        predicate(is_time, "is_month"),
    ),
    prod=_the_dom_of_month_prod,
)

_the_dom_of_month_num_rule = Rule(
    name="the <dom> of <month> (numeral)",
    pattern=(
        regex(r"the"),
        predicate(is_numeral, "is_dom"),
        regex(r"of|in"),
        predicate(is_time, "is_month"),
    ),
    prod=_the_dom_of_month_prod,
)


def _dom_regex_of_month_prod(tokens: tuple[Token, ...]) -> Token | None:
    dom_tok = tokens[0]
    month_tok = tokens[-1]
    n = _dom_from_token(dom_tok)
    if n is None or not _is_month_grain(month_tok):
        return None
    return _tt(with_day_of_month(month_tok.value, n))


_DOM_REGEX = (
    r"(?:[12]\d|3[01]|0?[1-9])(?:st|nd|rd|th)?"
    + "|"
    + "|".join(sorted(ORDINAL_WORDS.keys(), key=len, reverse=True))
)

_dom_regex_of_month_rule = Rule(
    name="<dom-regex> of <month>",
    pattern=(
        regex(_DOM_REGEX),
        regex(r"of|in"),
        predicate(is_time, "is_month"),
    ),
    prod=_dom_regex_of_month_prod,
)

_dom_regex_month_rule = Rule(
    name="<dom-regex> <month>",
    pattern=(
        regex(_DOM_REGEX),
        predicate(is_time, "is_month"),
    ),
    prod=_dom_regex_of_month_prod,
)


def _month_dom_regex_prod_2(tokens: tuple[Token, ...]) -> Token | None:
    """`<month> <dom-regex>` — supports both numeric and word ordinals."""
    month_tok = tokens[0]
    dom_tok = tokens[-1]
    if not _is_month_grain(month_tok):
        return None
    n = _dom_from_token(dom_tok)
    if n is None:
        return None
    return _tt(with_day_of_month(month_tok.value, n))


_month_dom_regex_extra_rule = Rule(
    name="<month> <dom-regex (word ord)>",
    pattern=(
        predicate(is_time, "is_month"),
        regex(_DOM_REGEX),
    ),
    prod=_month_dom_regex_prod_2,
)


_month_the_dom_regex_rule = Rule(
    name="<month> the <dom-regex>",
    pattern=(
        predicate(is_time, "is_month"),
        regex(r"the"),
        regex(_DOM_REGEX),
    ),
    prod=_month_dom_regex_prod_2,
)


def _the_dom_regex_of_month_prod(tokens: tuple[Token, ...]) -> Token | None:
    """e.g. 'the 1st of march', 'the third of march'."""
    dom_tok = tokens[1]
    month_tok = tokens[-1]
    if not _is_month_grain(month_tok):
        return None
    n = _dom_from_token(dom_tok)
    if n is None:
        return None
    return _tt(with_day_of_month(month_tok.value, n))


_the_dom_regex_of_month_rule = Rule(
    name="the <dom-regex> of <month>",
    pattern=(
        regex(r"the"),
        regex(_DOM_REGEX),
        regex(r"of|in"),
        predicate(is_time, "is_month"),
    ),
    prod=_the_dom_regex_of_month_prod,
)


# "<dom> <month> <year>" — month-year suffix variant
def _dom_month_year_prod(tokens: tuple[Token, ...]) -> Token | None:
    dom_tok, month_tok, year_match = tokens
    if not _is_month_grain(month_tok):
        return None
    n = _dom_from_token(dom_tok)
    if n is None:
        return None
    if not isinstance(year_match.value, RegexMatch):
        return None
    try:
        y = int(year_match.value.text)
    except ValueError:
        return None
    if y < 70:
        y += 2000
    elif y < 100:
        y += 1900
    rt = with_day_of_month(month_tok.value, n)
    return _tt(at_year_in(rt, y))


_dom_month_year_rule = Rule(
    name="<dom> <month> <year>",
    pattern=(
        predicate(lambda t: _dom_from_token(t) is not None, "is_dom"),
        predicate(is_time, "is_month"),
        regex(r"\d{2,4}"),
    ),
    prod=_dom_month_year_prod,
)


# "<month> <day> <year>"
def _month_dom_year_prod(tokens: tuple[Token, ...]) -> Token | None:
    month_tok, dom_tok, year_match = tokens
    if not _is_month_grain(month_tok):
        return None
    n = _dom_from_token(dom_tok)
    if n is None:
        return None
    if not isinstance(year_match.value, RegexMatch):
        return None
    try:
        y = int(year_match.value.text)
    except ValueError:
        return None
    if y < 70:
        y += 2000
    elif y < 100:
        y += 1900
    rt = with_day_of_month(month_tok.value, n)
    return _tt(at_year_in(rt, y))


_month_dom_year_rule = Rule(
    name="<month> <dom> <year>",
    pattern=(
        predicate(is_time, "is_month"),
        predicate(lambda t: _dom_from_token(t) is not None, "is_dom"),
        regex(r"\d{2,4}"),
    ),
    prod=_month_dom_year_prod,
)


def _month_dom_regex_year_prod(tokens: tuple[Token, ...]) -> Token | None:
    month_tok = tokens[0]
    dom_match = tokens[1].value
    year_match = tokens[2].value
    if not _is_month_grain(month_tok):
        return None
    if not isinstance(dom_match, RegexMatch) or not isinstance(year_match, RegexMatch):
        return None
    n = _dom_from_token(tokens[1])
    if n is None:
        return None
    try:
        y = int(year_match.text)
    except ValueError:
        return None
    if y < 70:
        y += 2000
    elif y < 100:
        y += 1900
    rt = with_day_of_month(month_tok.value, n)
    return _tt(at_year_in(rt, y))


_month_dom_regex_year_rule = Rule(
    name="<month> <dom-regex> <year>",
    pattern=(
        predicate(is_time, "is_month"),
        regex(r"(?:[12]\d|3[01]|0?[1-9])(?:st|nd|rd|th)?"),
        regex(r"\d{2,4}"),
    ),
    prod=_month_dom_regex_year_prod,
)


def _dom_regex_month_year_prod(tokens: tuple[Token, ...]) -> Token | None:
    dom_match = tokens[0].value
    month_tok = tokens[1]
    year_match = tokens[2].value
    if not _is_month_grain(month_tok):
        return None
    if not isinstance(dom_match, RegexMatch) or not isinstance(year_match, RegexMatch):
        return None
    n = _dom_from_token(tokens[0])
    if n is None:
        return None
    try:
        y = int(year_match.text)
    except ValueError:
        return None
    if y < 70:
        y += 2000
    elif y < 100:
        y += 1900
    rt = with_day_of_month(month_tok.value, n)
    return _tt(at_year_in(rt, y))


_dom_regex_month_year_rule = Rule(
    name="<dom-regex> <month> <year>",
    pattern=(
        regex(r"(?:[12]\d|3[01]|0?[1-9])(?:st|nd|rd|th)?"),
        predicate(is_time, "is_month"),
        regex(r"\d{2,4}"),
    ),
    prod=_dom_regex_month_year_prod,
)


# ---------------------------------------------------------------------------
# Cycles: "this/last/next week|month|year|quarter|day"


CYCLE_GRAINS = {
    "second": Grain.SECOND,
    "minute": Grain.MINUTE,
    "hour": Grain.HOUR,
    "day": Grain.DAY,
    "week": Grain.WEEK,
    "month": Grain.MONTH,
    "quarter": Grain.QUARTER,
    "qtr": Grain.QUARTER,
    "year": Grain.YEAR,
    "yr": Grain.YEAR,
}


def _cycle_offset_prod(tokens: tuple[Token, ...]) -> Token | None:
    direction_match = tokens[0].value
    grain_match = tokens[1].value
    if not isinstance(direction_match, RegexMatch) or not isinstance(grain_match, RegexMatch):
        return None
    direction = direction_match.text.lower()
    grain_text = grain_match.text.lower().rstrip("s")
    if grain_text not in CYCLE_GRAINS:
        return None
    grain = CYCLE_GRAINS[grain_text]
    n = {
        "this": 0,
        "current": 0,
        "the": 0,
        "coming": 1,
        "next": 1,
        "upcoming": 1,
        "the following": 1,
        "last": -1,
        "past": -1,
        "previous": -1,
    }.get(direction)
    if n is None:
        return None
    return _tt(cycle_nth(grain, n))


_cycle_rule = Rule(
    name="this|last|next <cycle>",
    pattern=(
        regex(r"this|current|coming|next|the following|last|past|previous|upcoming"),
        regex(r"seconds?|minutes?|hours?|days?|weeks?|months?|quarters?|qtrs?|years?|yrs?"),
    ),
    prod=_cycle_offset_prod,
)


# Standalone "<grain>s" doesn't resolve in EN base rules, but supporting
# "this week", "next month" already covered above. We support a bare regex
# for "the week" (latent) per corpus expectations.

# ---------------------------------------------------------------------------
# Day-of-week with this/next/last/after-next prefix


def _is_named_dow(t: Token) -> bool:
    """True iff `t` is a RelTime built by `day_of_week_relative` (a weekday name)."""
    if t.dim != "time":
        return False
    rt = t.value
    if not hasattr(rt, "key"):
        return False
    return bool(rt.key) and rt.key[0] == "dow_rel"


def _next_dow_prod(tokens: tuple[Token, ...]) -> Token | None:
    direction_match = tokens[0].value
    dow_tok = tokens[1]
    if not isinstance(direction_match, RegexMatch):
        return None
    direction = direction_match.text.lower()
    if not _is_named_dow(dow_tok):
        return None
    rt = dow_tok.value
    weekday = rt.key[1] if len(rt.key) > 1 else None
    if weekday is None:
        return None
    if direction == "this":
        return _tt(day_of_week_relative(weekday))
    if direction == "next":
        return _tt(next_day_of_week(weekday))
    if direction in ("last", "past", "previous", "this past"):
        return _tt(last_day_of_week(weekday))
    return None


_next_dow_rule = Rule(
    name="this|next|last <day-of-week>",
    pattern=(
        regex(r"this past|this|next|last|past|previous"),
        predicate(_is_named_dow, "is_named_dow"),
    ),
    prod=_next_dow_prod,
)


# ---------------------------------------------------------------------------
# Clock times: "<H>:<M>", "<H>am", "<H> o'clock"


def _hhmm_prod(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[0].value
    if not isinstance(m, RegexMatch):
        return None
    try:
        h = int(m.groups[0])
        mn = int(m.groups[1])
    except (ValueError, IndexError):
        return None
    return _tt(hour_minute_value(h, mn, is_12h=(h != 0 and h < 12)))


_hhmm_rule = Rule(
    name="hh:mm",
    pattern=(regex(r"((?:[01]?\d)|(?:2[0-3]))[:.]([0-5]\d)(?!\d)"),),
    prod=_hhmm_prod,
)


def _hhmmss_prod(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[0].value
    if not isinstance(m, RegexMatch):
        return None
    try:
        h = int(m.groups[0])
        mn = int(m.groups[1])
        s = int(m.groups[2])
    except (ValueError, IndexError):
        return None
    return _tt(hour_minute_second_value(h, mn, s, is_12h=(h < 12)))


_hhmmss_rule = Rule(
    name="hh:mm:ss",
    pattern=(regex(r"((?:[01]?\d)|(?:2[0-3]))[:.]([0-5]\d)[:.]([0-5]\d)"),),
    prod=_hhmmss_prod,
)


def _hhmm_am_pm_prod(tokens: tuple[Token, ...]) -> Token | None:
    """e.g. '3:18am', '11:45pm', '5pm' (minutes optional)."""
    digits = tokens[0].value
    suffix = tokens[1].value
    if not isinstance(digits, RegexMatch) or not isinstance(suffix, RegexMatch):
        return None
    try:
        h = int(digits.groups[0])
    except (ValueError, IndexError):
        return None
    has_minutes = digits.groups[1] is not None
    mn = int(digits.groups[1]) if has_minutes else 0
    is_am = suffix.text.lower().startswith("a")
    if h > 12:
        return None
    final_h = h % 12 + (0 if is_am else 12)
    if has_minutes:
        return _tt(hour_minute_value(final_h, mn, is_12h=False))
    return _tt(hour_value(final_h, is_12h=False))


_hhmm_ampm_rule = Rule(
    name="hh:mm am/pm",
    pattern=(
        regex(r"((?:1[012]|0?[1-9]))(?:[:.]([0-5]\d))?"),
        regex(r"([ap])\.?m?\.?"),
    ),
    prod=_hhmm_am_pm_prod,
)


def _bare_hour_am_pm_prod(tokens: tuple[Token, ...]) -> Token | None:
    """e.g. '3pm', '11am'."""
    digits = tokens[0].value
    suffix = tokens[1].value
    if not isinstance(digits, RegexMatch) or not isinstance(suffix, RegexMatch):
        return None
    try:
        h = int(digits.text)
    except ValueError:
        return None
    if h < 1 or h > 12:
        return None
    is_am = suffix.text.lower().startswith("a")
    final_h = h % 12 + (0 if is_am else 12)
    return _tt(hour_value(final_h, is_12h=False))


_bare_hour_ampm_rule = Rule(
    name="<H> am/pm",
    pattern=(regex(r"(?:1[012]|0?[1-9])"), regex(r"([ap])\.?m?\.?")),
    prod=_bare_hour_am_pm_prod,
)


def _hour_oclock_prod(tokens: tuple[Token, ...]) -> Token | None:
    digits = tokens[0].value
    if not isinstance(digits, RegexMatch):
        return None
    try:
        h = int(digits.text)
    except ValueError:
        return None
    if h < 1 or h > 23:
        return None
    return _tt(hour_value(h, is_12h=(h <= 12)))


_hour_oclock_rule = Rule(
    name="<H> o'clock",
    pattern=(regex(r"\d{1,2}"), regex(r"o.?clock")),
    prod=_hour_oclock_prod,
)


_HOUR_WORDS = (
    "one", "two", "three", "four", "five", "six",
    "seven", "eight", "nine", "ten", "eleven", "twelve",
)
_HOUR_WORD_PATTERN = "|".join(_HOUR_WORDS)


def _word_hour_am_pm_prod(tokens: tuple[Token, ...]) -> Token | None:
    digits = tokens[0].value
    suffix = tokens[1].value
    if not isinstance(digits, RegexMatch) or not isinstance(suffix, RegexMatch):
        return None
    h = WORD_NUMS.get(digits.text.lower())
    if h is None:
        return None
    is_am = suffix.text.lower().startswith("a")
    final_h = h % 12 + (0 if is_am else 12)
    return _tt(hour_value(final_h, is_12h=False))


_word_hour_ampm_rule = Rule(
    name="<word-H> am/pm",
    pattern=(regex(_HOUR_WORD_PATTERN), regex(r"([ap])\.?m?\.?")),
    prod=_word_hour_am_pm_prod,
)


def _word_hour_oclock_prod(tokens: tuple[Token, ...]) -> Token | None:
    digits = tokens[0].value
    if not isinstance(digits, RegexMatch):
        return None
    h = WORD_NUMS.get(digits.text.lower())
    if h is None:
        return None
    return _tt(hour_value(h, is_12h=True))


_word_hour_oclock_rule = Rule(
    name="<word-H> o'clock",
    pattern=(regex(_HOUR_WORD_PATTERN), regex(r"o.?clock")),
    prod=_word_hour_oclock_prod,
)


def _bare_word_hour_prod(tokens: tuple[Token, ...]) -> Token | None:
    """A latent hour from a word numeral (e.g. 'three', 'eight')."""
    digits = tokens[0].value
    if not isinstance(digits, RegexMatch):
        return None
    h = WORD_NUMS.get(digits.text.lower())
    if h is None:
        return None
    return _tt(hour_value(h, is_12h=True, latent=True))


_bare_word_hour_rule = Rule(
    name="<word-H> (latent hour)",
    pattern=(regex(_HOUR_WORD_PATTERN),),
    prod=_bare_word_hour_prod,
)


def _at_tod_prod(tokens: tuple[Token, ...]) -> Token | None:
    inner = tokens[1]
    if inner.dim != "time":
        return None
    rt: RelTime = inner.value
    return _tt(rt.not_latent())


_at_tod_rule = Rule(
    name="at <time-of-day>",
    pattern=(regex(r"at|@"), predicate(is_time, "is_time")),
    prod=_at_tod_prod,
)


def _noon_midnight_prod(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[0].value
    if not isinstance(m, RegexMatch):
        return None
    text = m.text.lower()
    if "noon" in text:
        return _tt(hour_value(12, is_12h=False))
    return _tt(hour_value(0, is_12h=False))


_noon_midnight_rule = Rule(
    name="noon|midnight",
    pattern=(regex(r"noon|midni(ght|te)|EOD|end of (the )?day"),),
    prod=_noon_midnight_prod,
)


# half / quarter relative to hour — e.g. "half past 3", "quarter to noon"
def _half_past_prod(tokens: tuple[Token, ...]) -> Token | None:
    inner = tokens[1]
    if inner.dim != "time":
        return None
    return _tt(shift_minutes(inner.value, 30))


_half_past_rule = Rule(
    name="half past <H>",
    pattern=(regex(r"half\s+(past|after)"), predicate(_is_hour_or_minute, "is_hour")),
    prod=_half_past_prod,
)


def _quarter_past_prod(tokens: tuple[Token, ...]) -> Token | None:
    inner = tokens[1]
    if inner.dim != "time":
        return None
    return _tt(shift_minutes(inner.value, 15))


_quarter_past_rule = Rule(
    name="quarter past <H>",
    pattern=(
        regex(r"(?:a\s+)?quarter\s+(past|after)"),
        predicate(_is_hour_or_minute, "is_hour"),
    ),
    prod=_quarter_past_prod,
)


def _quarter_to_prod(tokens: tuple[Token, ...]) -> Token | None:
    inner = tokens[1]
    if inner.dim != "time":
        return None
    return _tt(shift_minutes(inner.value, -15))


_quarter_to_rule = Rule(
    name="quarter to <H>",
    pattern=(
        regex(r"(?:a\s+)?quarter\s+(to|till|before|of)"),
        predicate(_is_hour_or_minute, "is_hour"),
    ),
    prod=_quarter_to_prod,
)


def _half_to_prod(tokens: tuple[Token, ...]) -> Token | None:
    inner = tokens[1]
    if inner.dim != "time":
        return None
    return _tt(shift_minutes(inner.value, -30))


_half_to_rule = Rule(
    name="half to <H>",
    pattern=(
        regex(r"half\s+(to|till|before|of)"),
        predicate(_is_hour_or_minute, "is_hour"),
    ),
    prod=_half_to_prod,
)


def _n_past_hour_prod(tokens: tuple[Token, ...]) -> Token | None:
    n = _natural_int(tokens[0])
    inner = tokens[2]
    if n is None or inner.dim != "time" or not 1 <= n <= 59:
        return None
    return _tt(shift_minutes(inner.value, n))


_n_past_hour_rule = Rule(
    name="<n> past <H>",
    pattern=(
        predicate(is_numeral, "is_natural"),
        regex(r"past|after"),
        predicate(_is_hour_or_minute, "is_hour"),
    ),
    prod=_n_past_hour_prod,
)


def _n_to_hour_prod(tokens: tuple[Token, ...]) -> Token | None:
    n = _natural_int(tokens[0])
    inner = tokens[2]
    if n is None or inner.dim != "time" or not 1 <= n <= 59:
        return None
    return _tt(shift_minutes(inner.value, -n))


_n_to_hour_rule = Rule(
    name="<n> to <H>",
    pattern=(
        predicate(is_numeral, "is_natural"),
        regex(r"to|till|before|of"),
        predicate(_is_hour_or_minute, "is_hour"),
    ),
    prod=_n_to_hour_prod,
)


def _bare_n_past_hour_prod(tokens: tuple[Token, ...]) -> Token | None:
    digits = tokens[0].value
    inner = tokens[2]
    if not isinstance(digits, RegexMatch) or inner.dim != "time":
        return None
    n = _parse_int_word(digits.text)
    if n is None or not 1 <= n <= 59:
        return None
    return _tt(shift_minutes(inner.value, n))


_bare_n_past_hour_rule = Rule(
    name="<n-regex> past <H>",
    pattern=(
        regex(r"\d{1,2}|" + "|".join(WORD_NUMS.keys())),
        regex(r"past|after"),
        predicate(_is_hour_or_minute, "is_hour"),
    ),
    prod=_bare_n_past_hour_prod,
)


def _bare_n_to_hour_prod(tokens: tuple[Token, ...]) -> Token | None:
    digits = tokens[0].value
    inner = tokens[2]
    if not isinstance(digits, RegexMatch) or inner.dim != "time":
        return None
    n = _parse_int_word(digits.text)
    if n is None or not 1 <= n <= 59:
        return None
    return _tt(shift_minutes(inner.value, -n))


_bare_n_to_hour_rule = Rule(
    name="<n-regex> to <H>",
    pattern=(
        regex(r"\d{1,2}|" + "|".join(WORD_NUMS.keys())),
        regex(r"to|till|before|of"),
        predicate(_is_hour_or_minute, "is_hour"),
    ),
    prod=_bare_n_to_hour_prod,
)


# ---------------------------------------------------------------------------
# Parts of day


def _make_pod_rule(name: str, pat: str, start_h: int, end_h: int) -> Rule:
    def prod(_: tuple[Token, ...]) -> Token | None:
        return _tt(_pod_interval(start_h, end_h))

    return Rule(name=name, pattern=(regex(pat),), prod=prod)


def _pod_interval(start_h: int, end_h: int) -> RelTime:
    """Build a part-of-day interval where hours wrap past midnight if needed."""


    def go(ref: dt.datetime):
        ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
        start = InstantValue(value=ref_day.replace(hour=start_h), grain=Grain.HOUR)
        if end_h == 0:
            end_value = ref_day + dt.timedelta(days=1)
        elif end_h <= start_h:
            end_value = ref_day + dt.timedelta(days=1, hours=end_h)
        else:
            end_value = ref_day.replace(hour=end_h)
        end = InstantValue(value=end_value, grain=Grain.HOUR)
        return IntervalValue(start=start, end=end)

    return RelTime(
        compute=go,
        grain=Grain.HOUR,
        latent=True,
        key=("pod_interval", start_h, end_h),
    )


_morning_rule = _make_pod_rule("morning", r"morning", 0, 12)
_afternoon_rule = _make_pod_rule("afternoon", r"after\s?noo?n(ish)?", 12, 19)
_evening_rule = _make_pod_rule("evening", r"evening", 18, 0)
_night_rule = _make_pod_rule("night", r"night", 18, 0)


def _tonight_prod(_: tuple[Token, ...]) -> Token | None:
    """Tonight: today, 18:00 - midnight."""


    def go(ref: dt.datetime):
        ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
        start = InstantValue(value=ref_day.replace(hour=18), grain=Grain.HOUR)
        end = InstantValue(value=ref_day + dt.timedelta(days=1), grain=Grain.HOUR)
        return IntervalValue(start=start, end=end)

    return _tt(RelTime(compute=go, grain=Grain.HOUR, key=("tonight",)))


_tonight_rule = Rule(
    name="tonight",
    pattern=(regex(r"toni(ght|gth|te)"),),
    prod=_tonight_prod,
)


# "this evening / this morning"
def _this_part_of_day_prod(tokens: tuple[Token, ...]) -> Token | None:
    inner = tokens[1]
    if inner.dim != "time":
        return None
    rt: RelTime = inner.value
    return _tt(rt.not_latent())


_this_part_of_day_rule = Rule(
    name="this <part-of-day>",
    pattern=(regex(r"this|today"), predicate(is_time, "is_pod")),
    prod=_this_part_of_day_prod,
)


# ---------------------------------------------------------------------------
# Last night / yesterday evening — a 6h block ending at start-of-today.
def _last_night_prod(tokens: tuple[Token, ...]) -> Token | None:


    m = tokens[0].value
    late = isinstance(m, RegexMatch) and "late" in m.text.lower()
    hours = 3 if late else 6

    def go(ref: dt.datetime):
        ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
        start = InstantValue(value=ref_day - dt.timedelta(hours=hours), grain=Grain.HOUR)
        end = InstantValue(value=ref_day, grain=Grain.HOUR)
        return IntervalValue(start=start, end=end)

    return _tt(RelTime(compute=go, grain=Grain.HOUR, key=("last_night", late)))


_last_night_rule = Rule(
    name="last night",
    pattern=(regex(r"(late\s+)?(last night|yesterday evening)"),),
    prod=_last_night_prod,
)


# ---------------------------------------------------------------------------
# Weekend / week interval


def _weekend_prod(_: tuple[Token, ...]) -> Token | None:
    """The next weekend interval — Saturday 00:00 .. Monday 00:00."""


    def go(ref: dt.datetime):
        ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
        days_to_sat = (5 - ref_day.weekday()) % 7
        sat = ref_day + dt.timedelta(days=days_to_sat)
        end = sat + dt.timedelta(days=2)
        return IntervalValue(
            start=InstantValue(value=sat, grain=Grain.DAY),
            end=InstantValue(value=end, grain=Grain.DAY),
        )

    return _tt(RelTime(compute=go, grain=Grain.DAY, key=("weekend",)))


_weekend_rule = Rule(
    name="weekend",
    pattern=(regex(r"(week(\s|-)?end|wkend)s?"),),
    prod=_weekend_prod,
)


def _the_week_prod(_: tuple[Token, ...]) -> Token | None:
    """'the week' — interval from today until the end of the current week."""


    def go(ref: dt.datetime):
        ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
        # End of current week (Saturday end-of-day = Sunday 00:00).
        days_until_next_monday = 7 - ref_day.weekday()
        next_monday = ref_day + dt.timedelta(days=days_until_next_monday)
        return IntervalValue(
            start=InstantValue(value=ref_day, grain=Grain.DAY),
            end=InstantValue(value=next_monday, grain=Grain.DAY),
        )

    return _tt(RelTime(compute=go, grain=Grain.DAY, latent=True, key=("the_week",)))


_the_week_rule = Rule(
    name="the week",
    pattern=(regex(r"the week"),),
    prod=_the_week_prod,
)


# ---------------------------------------------------------------------------
# "in <duration>" / "<duration> ago" / "<n> days ago" / "<n> days from now"


def _in_n_grain_prod(tokens: tuple[Token, ...]) -> Token | None:
    """Match patterns: "in <n> <grain>" or "<n> <grain> from now"."""
    n_tok = tokens[1]
    grain_tok = tokens[2]
    n = _natural_int(n_tok)
    if n is None:
        return None
    if not isinstance(grain_tok.value, RegexMatch):
        return None
    grain_text = grain_tok.value.text.lower().rstrip("s")
    grain = CYCLE_GRAINS.get(grain_text)
    if grain is None:
        return None
    return _tt(_offset_now(grain, n))


def _offset_now(grain: Grain, n: int) -> RelTime:
    """Mirrors Duckling's `inDuration` — shifts the reference by n*grain.

    The resulting grain follows Duckling's conventions:
    - day/week/month/year shifts → hour grain (date-aware)
    - hour shifts → minute grain
    - finer shifts → second grain
    """


    def go(ref: dt.datetime):
        shifted = add_grain(ref, grain, n)
        return InstantValue(value=_truncate_for(shifted, grain), grain=_finest_grain(grain))

    return RelTime(
        compute=go,
        grain=_finest_grain(grain),
        key=("offset_now", grain.value, n),
    )


def _truncate_for(d, grain: Grain):
    """Truncate `d` to the relevant precision for an `_offset_now` result."""
    if grain is Grain.YEAR:
        return d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if grain is Grain.MONTH:
        return d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if grain is Grain.WEEK:
        return d.replace(hour=0, minute=0, second=0, microsecond=0)
    if grain is Grain.DAY:
        return d.replace(minute=0, second=0, microsecond=0)
    if grain is Grain.HOUR:
        return d.replace(second=0, microsecond=0)
    return d.replace(microsecond=0)


def _finest_grain(g: Grain) -> Grain:
    """The grain of the resolved value after an `inDuration`-style shift."""
    if g is Grain.YEAR:
        return Grain.MONTH
    if g is Grain.MONTH:
        return Grain.MONTH
    if g is Grain.WEEK:
        return Grain.DAY
    if g is Grain.DAY:
        return Grain.HOUR
    if g is Grain.HOUR:
        return Grain.MINUTE
    return Grain.SECOND


_in_n_grain_rule = Rule(
    name="in <n> <grain>",
    pattern=(
        regex(r"in"),
        predicate(is_numeral, "is_n"),
        regex(r"seconds?|minutes?|hours?|days?|weeks?|months?|years?"),
    ),
    prod=_in_n_grain_prod,
)


def _parse_int_word(text: str) -> int | None:
    text = text.strip().lower()
    if text in WORD_NUMS:
        return WORD_NUMS[text]
    if text.isdigit():
        return int(text)
    return None


def _in_digits_grain_prod(tokens: tuple[Token, ...]) -> Token | None:
    digits = tokens[1].value
    grain_tok = tokens[2]
    if not isinstance(digits, RegexMatch) or not isinstance(grain_tok.value, RegexMatch):
        return None
    n = _parse_int_word(digits.text)
    if n is None:
        return None
    grain = CYCLE_GRAINS.get(grain_tok.value.text.lower().rstrip("s"))
    if grain is None:
        return None
    return _tt(_offset_now(grain, n))


_in_digits_grain_rule = Rule(
    name="in <digits> <grain>",
    pattern=(
        regex(r"in"),
        regex(r"\d+|" + "|".join(WORD_NUMS.keys())),
        regex(r"seconds?|minutes?|hours?|days?|weeks?|months?|years?"),
    ),
    prod=_in_digits_grain_prod,
)


def _digits_grain_ago_prod(tokens: tuple[Token, ...]) -> Token | None:
    digits = tokens[0].value
    grain_tok = tokens[1]
    if not isinstance(digits, RegexMatch) or not isinstance(grain_tok.value, RegexMatch):
        return None
    n = _parse_int_word(digits.text)
    if n is None:
        return None
    grain = CYCLE_GRAINS.get(grain_tok.value.text.lower().rstrip("s"))
    if grain is None:
        return None
    return _tt(_offset_now(grain, -n))


_digits_grain_ago_rule = Rule(
    name="<digits> <grain> ago",
    pattern=(
        regex(r"\d+|" + "|".join(WORD_NUMS.keys())),
        regex(r"seconds?|minutes?|hours?|days?|weeks?|months?|years?"),
        regex(r"ago|back"),
    ),
    prod=_digits_grain_ago_prod,
)


def _digits_grain_from_now_prod(tokens: tuple[Token, ...]) -> Token | None:
    digits = tokens[0].value
    grain_tok = tokens[1]
    if not isinstance(digits, RegexMatch) or not isinstance(grain_tok.value, RegexMatch):
        return None
    n = _parse_int_word(digits.text)
    if n is None:
        return None
    grain = CYCLE_GRAINS.get(grain_tok.value.text.lower().rstrip("s"))
    if grain is None:
        return None
    return _tt(_offset_now(grain, n))


_digits_grain_from_now_rule = Rule(
    name="<digits> <grain> from now",
    pattern=(
        regex(r"\d+|" + "|".join(WORD_NUMS.keys())),
        regex(r"seconds?|minutes?|hours?|days?|weeks?|months?|years?"),
        regex(r"from now|hence"),
    ),
    prod=_digits_grain_from_now_prod,
)


def _n_dow_from_now_prod(tokens: tuple[Token, ...]) -> Token | None:
    """e.g. '3 fridays from now' — the n-th Friday from today."""
    digits = tokens[0].value
    dow_tok = tokens[1]
    if not isinstance(digits, RegexMatch):
        return None
    n = _parse_int_word(digits.text)
    if n is None or not _is_named_dow(dow_tok):
        return None
    weekday = dow_tok.value.key[1] if len(dow_tok.value.key) > 1 else None
    if weekday is None:
        return None



    def go(ref: dt.datetime):
        ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
        delta = (weekday - ref_day.weekday()) % 7
        # The first occurrence is delta days away; the n-th is (delta + 7*(n-1)) away.
        # Skip today even if it matches (Duckling's "from now" semantics).
        if delta == 0:
            delta = 7
        target = ref_day + dt.timedelta(days=delta + 7 * (n - 1))
        return InstantValue(value=target, grain=Grain.DAY)

    return _tt(RelTime(compute=go, grain=Grain.DAY, key=("n_dow_fwd", n, weekday)))


_n_dow_from_now_rule = Rule(
    name="<n> <day-of-week> from now",
    pattern=(
        regex(r"\d+|" + "|".join(WORD_NUMS.keys())),
        predicate(_is_named_dow, "is_named_dow"),
        regex(r"from now|hence"),
    ),
    prod=_n_dow_from_now_prod,
)


def _n_dow_ago_prod(tokens: tuple[Token, ...]) -> Token | None:
    digits = tokens[0].value
    dow_tok = tokens[1]
    if not isinstance(digits, RegexMatch):
        return None
    n = _parse_int_word(digits.text)
    if n is None or not _is_named_dow(dow_tok):
        return None
    weekday = dow_tok.value.key[1] if len(dow_tok.value.key) > 1 else None
    if weekday is None:
        return None



    def go(ref: dt.datetime):
        ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
        delta = (ref_day.weekday() - weekday) % 7
        if delta == 0:
            delta = 7
        target = ref_day - dt.timedelta(days=delta + 7 * (n - 1))
        return InstantValue(value=target, grain=Grain.DAY)

    return _tt(RelTime(compute=go, grain=Grain.DAY, key=("n_dow_back", n, weekday)))


_n_dow_ago_rule = Rule(
    name="<n> <day-of-week> ago",
    pattern=(
        regex(r"\d+|" + "|".join(WORD_NUMS.keys())),
        predicate(_is_named_dow, "is_named_dow"),
        regex(r"ago|back"),
    ),
    prod=_n_dow_ago_prod,
)


def _n_grain_from_now_prod(tokens: tuple[Token, ...]) -> Token | None:
    n = _natural_int(tokens[0])
    grain_tok = tokens[1]
    if n is None or not isinstance(grain_tok.value, RegexMatch):
        return None
    grain_text = grain_tok.value.text.lower().rstrip("s")
    grain = CYCLE_GRAINS.get(grain_text)
    if grain is None:
        return None
    return _tt(_offset_now(grain, n))


_n_grain_from_now_rule = Rule(
    name="<n> <grain> from now",
    pattern=(
        predicate(is_numeral, "is_n"),
        regex(r"seconds?|minutes?|hours?|days?|weeks?|months?|years?"),
        regex(r"from now|hence"),
    ),
    prod=_n_grain_from_now_prod,
)


def _n_grain_ago_prod(tokens: tuple[Token, ...]) -> Token | None:
    n = _natural_int(tokens[0])
    grain_tok = tokens[1]
    if n is None or not isinstance(grain_tok.value, RegexMatch):
        return None
    grain_text = grain_tok.value.text.lower().rstrip("s")
    grain = CYCLE_GRAINS.get(grain_text)
    if grain is None:
        return None
    return _tt(_offset_now(grain, -n))


_n_grain_ago_rule = Rule(
    name="<n> <grain> ago",
    pattern=(
        predicate(is_numeral, "is_n"),
        regex(r"seconds?|minutes?|hours?|days?|weeks?|months?|years?"),
        regex(r"ago|back"),
    ),
    prod=_n_grain_ago_prod,
)


def _a_grain_ago_prod(tokens: tuple[Token, ...]) -> Token | None:
    grain_tok = tokens[1]
    if not isinstance(grain_tok.value, RegexMatch):
        return None
    grain_text = grain_tok.value.text.lower().rstrip("s")
    grain = CYCLE_GRAINS.get(grain_text)
    if grain is None:
        return None
    return _tt(_offset_now(grain, -1))


_a_grain_ago_rule = Rule(
    name="a <grain> ago",
    pattern=(
        regex(r"an?|one"),
        regex(r"second|minute|hour|day|week|month|year"),
        regex(r"ago|back"),
    ),
    prod=_a_grain_ago_prod,
)


def _in_a_grain_prod(tokens: tuple[Token, ...]) -> Token | None:
    grain_tok = tokens[2]
    if not isinstance(grain_tok.value, RegexMatch):
        return None
    grain_text = grain_tok.value.text.lower().rstrip("s")
    grain = CYCLE_GRAINS.get(grain_text)
    if grain is None:
        return None
    return _tt(_offset_now(grain, 1))


_in_a_grain_rule = Rule(
    name="in a <grain>",
    pattern=(
        regex(r"in"),
        regex(r"an?|one"),
        regex(r"second|minute|hour|day|week|month|year"),
    ),
    prod=_in_a_grain_prod,
)


# ---------------------------------------------------------------------------
# Intervals: "between <X> and <Y>", "from <X> to <Y>", "<X> - <Y>"


def _between_and_prod(tokens: tuple[Token, ...]) -> Token | None:
    a = tokens[1]
    b = tokens[3]
    if a.dim != "time" or b.dim != "time":
        return None
    return _tt(interval(a.value, b.value))


_between_and_rule = Rule(
    name="between <X> and <Y>",
    pattern=(
        regex(r"between"),
        predicate(is_time, "is_time"),
        regex(r"and"),
        predicate(is_time, "is_time"),
    ),
    prod=_between_and_prod,
)


def _from_to_prod(tokens: tuple[Token, ...]) -> Token | None:
    a = tokens[1]
    b = tokens[3]
    if a.dim != "time" or b.dim != "time":
        return None
    return _tt(interval(a.value, b.value))


_from_to_rule = Rule(
    name="from <X> to <Y>",
    pattern=(
        regex(r"from"),
        predicate(is_time, "is_time"),
        regex(r"to|until|till|through"),
        predicate(is_time, "is_time"),
    ),
    prod=_from_to_prod,
)


def _interval_dash_prod(tokens: tuple[Token, ...]) -> Token | None:
    a = tokens[0]
    b = tokens[2]
    if a.dim != "time" or b.dim != "time":
        return None
    return _tt(interval(a.value, b.value))


_interval_dash_rule = Rule(
    name="<X> - <Y>",
    pattern=(
        predicate(is_time, "is_time"),
        regex(r"\-|to|through|until|till"),
        predicate(is_time, "is_time"),
    ),
    prod=_interval_dash_prod,
)


def _until_prod(tokens: tuple[Token, ...]) -> Token | None:
    inner = tokens[1]
    if inner.dim != "time":
        return None
    return _tt(open_interval(inner.value, IntervalDirection.BEFORE))


_until_rule = Rule(
    name="until <X>",
    pattern=(regex(r"before|until|till|up to"), predicate(is_time, "is_time")),
    prod=_until_prod,
)


def _since_prod(tokens: tuple[Token, ...]) -> Token | None:
    inner = tokens[1]
    if inner.dim != "time":
        return None
    return _tt(open_interval(inner.value, IntervalDirection.AFTER))


_since_rule = Rule(
    name="since <X>",
    pattern=(regex(r"since|after|from"), predicate(is_time, "is_time")),
    prod=_since_prod,
)


# ---------------------------------------------------------------------------
# Holidays


def _fixed_holiday_rule(name: str, pat: str, month: int, day: int) -> Rule:
    def prod(_: tuple[Token, ...]) -> Token | None:
        return _tt(month_day(month, day, holiday=name))

    return Rule(name=f"holiday: {name}", pattern=(regex(pat),), prod=prod)


def _easter_holiday_rule(name: str, pat: str, offset_days: int, *, orthodox: bool = False) -> Rule:
    """A holiday computed as an offset from Easter Sunday."""


    def prod(_: tuple[Token, ...]) -> Token | None:
        def go(ref: dt.datetime):
            year = ref.year
            for candidate_year in (year, year + 1):
                base = orthodox_easter(candidate_year) if orthodox else easter(candidate_year)
                target = base + dt.timedelta(days=offset_days)
                target_dt = dt.datetime(target.year, target.month, target.day, tzinfo=ref.tzinfo)
                if target_dt >= ref.replace(hour=0, minute=0, second=0, microsecond=0):
                    return InstantValue(value=target_dt, grain=Grain.DAY)
            return None

        return _tt(
            RelTime(
                compute=go,
                grain=Grain.DAY,
                holiday=name,
                key=("easter_holiday", name, offset_days, orthodox),
            )
        )

    return Rule(name=f"holiday: {name}", pattern=(regex(pat),), prod=prod)


def _holidays_rules() -> tuple[Rule, ...]:
    fixed = (
        ("Africa Day", r"africa(n (freedom|liberation))? day", 5, 25),
        ("All Saints' Day", r"all saints' day", 11, 1),
        ("All Souls' Day", r"all souls' day", 11, 2),
        ("April Fools", r"(april|all) fool'?s('? day)?", 4, 1),
        ("Boxing Day", r"boxing day", 12, 26),
        ("Christmas", r"(xmas|christmas)( day)?", 12, 25),
        ("Christmas Eve", r"(xmas|christmas)( day)?('s)? eve", 12, 24),
        ("Earth Day", r"earth day", 4, 22),
        ("Epiphany", r"epiphany", 1, 6),
        ("Halloween", r"hall?owe?en( day)?", 10, 31),
        ("Independence Day", r"independence day", 7, 4),
        ("May Day", r"may day", 5, 1),
        ("New Year's Day", r"new year'?s?( day)?", 1, 1),
        ("New Year's Eve", r"new year'?s? eve", 12, 31),
        ("Orthodox Christmas Day", r"orthodox christmas( day)?", 1, 7),
        ("Orthodox New Year", r"orthodox new year", 1, 14),
        ("St Patrick's Day", r"(saint|st\.?) (patrick|paddy)'?s? day", 3, 17),
        ("St. George's Day", r"(saint|st\.?) george'?s day|feast of saint george", 4, 23),
        ("St. Stephen's Day", r"(saint|st\.?) stephen'?s day", 12, 26),
        ("Valentine's Day", r"valentine'?s?( day)?", 2, 14),
        ("World AIDS Day", r"world aids day", 12, 1),
        ("World Cancer Day", r"world cancer day", 2, 4),
        ("World Diabetes Day", r"world diabetes day", 11, 14),
        ("World Environment Day", r"world environment day", 6, 5),
        ("World Vegan Day", r"world vegan day", 11, 1),
        ("Women's Day", r"international women'?s day", 3, 8),
        ("Men's Day", r"international men'?s day", 11, 19),
    )

    rules = [_fixed_holiday_rule(n, p, m, d) for n, p, m, d in fixed]

    # Easter-based.
    rules.append(_easter_holiday_rule("Easter Sunday", r"easter(\s+sun(day)?)?", 0))
    rules.append(_easter_holiday_rule("Easter Monday", r"easter\s+mon(day)?", 1))
    rules.append(_easter_holiday_rule("Good Friday", r"(good|great|holy)\s+fri(day)?", -2))
    rules.append(_easter_holiday_rule("Palm Sunday", r"(branch|palm|yew)\s+sunday", -7))
    rules.append(_easter_holiday_rule("Holy Saturday", r"holy\s+sat(urday)?|easter eve", -1))
    rules.append(_easter_holiday_rule("Maundy Thursday", r"(covenant|holy|maundy|sheer)\s+thu(rsday)?|thursday of mysteries|covenant thu|thu of mysteries", -3))
    rules.append(_easter_holiday_rule("Pentecost", r"pentecost|whitsunday|white sunday", 49))
    rules.append(_easter_holiday_rule("Whit Monday", r"(pentecost|whit)\s+monday|monday of the holy spirit", 50))
    rules.append(_easter_holiday_rule("Trinity Sunday", r"trinity\s+sunday", 56))
    rules.append(_easter_holiday_rule("Ascension Day", r"ascension(\s+thurs)?day", 39))
    rules.append(_easter_holiday_rule("Ash Wednesday", r"ash\s+wednesday|carnival", -46))
    rules.append(_easter_holiday_rule("Shrove Tuesday", r"pancake (tues)?day|shrove tuesday|mardi gras", -47))
    rules.append(_easter_holiday_rule("Corpus Christi", r"(the feast of )?corpus\s+christi", 60))

    # Orthodox Easter-based.
    rules.append(_easter_holiday_rule("Orthodox Easter Sunday", r"orthodox\s+easter(\s+sun(day)?)?|pascha", 0, orthodox=True))
    rules.append(_easter_holiday_rule("Orthodox Easter Monday", r"orthodox\s+easter\s+mon(day)?", 1, orthodox=True))
    rules.append(_easter_holiday_rule("Orthodox Good Friday", r"orthodox\s+(great|good)\s+friday", -2, orthodox=True))
    rules.append(_easter_holiday_rule("Orthodox Palm Sunday", r"orthodox\s+(branch|palm|yew)\s+sunday", -7, orthodox=True))
    rules.append(_easter_holiday_rule("Clean Monday", r"(orthodox\s+)?(ash|clean|green|pure|shrove)\s+monday|monday of lent", -48, orthodox=True))
    rules.append(_easter_holiday_rule("Lazarus Saturday", r"lazarus\s+saturday", -8, orthodox=True))

    # Computed by month-week-weekday combinator (rough version).
    rules.append(_nth_dow_of_month_rule("Thanksgiving Day", r"thanksgiving(\s+day)?", 4, 3, 11))  # 4th Thu of Nov
    rules.append(_nth_dow_of_month_rule("Martin Luther King's Day", r"(MLK|martin luther king('?s)?,?)( jr\.?| junior)?\s+day|civil rights day", 3, 0, 1))
    rules.append(_nth_dow_of_month_rule("Black Friday", r"black\s+frid?day", 4, 4, 11, day_offset=1))
    rules.append(_nth_dow_of_month_rule("Mother's Day", r"mother'?s\s+day", 2, 6, 5))
    rules.append(_nth_dow_of_month_rule("Father's Day", r"father'?s\s+day", 3, 6, 6))
    rules.append(_nth_dow_of_month_rule("Labor Day", r"labor day", 1, 0, 9))

    return tuple(rules)


def _nth_dow_of_month_rule(
    name: str, pat: str, n: int, weekday: int, month: int, *, day_offset: int = 0
) -> Rule:
    """Holiday on the n-th given weekday of `month` (e.g. 4th Thursday of November)."""

    def prod(_: tuple[Token, ...]) -> Token | None:
    
    
        def go(ref: dt.datetime):
            for year_offset in (0, 1):
                year = ref.year + year_offset
                first = dt.date(year, month, 1)
                first_weekday = first.weekday()
                offset = (weekday - first_weekday) % 7
                day = 1 + offset + 7 * (n - 1) + day_offset
                try:
                    target = dt.datetime(year, month, day, tzinfo=ref.tzinfo)
                except ValueError:
                    continue
                if target >= ref.replace(hour=0, minute=0, second=0, microsecond=0):
                    return InstantValue(value=target, grain=Grain.DAY)
            return None

        return _tt(
            RelTime(
                compute=go,
                grain=Grain.DAY,
                holiday=name,
                key=("nth_dow_holiday", name, n, weekday, month, day_offset),
            )
        )

    return Rule(name=f"holiday: {name}", pattern=(regex(pat),), prod=prod)


# ---------------------------------------------------------------------------
# "<time> at <time-of-day>": e.g. "tomorrow at 5pm", "monday at 3pm"
def _time_at_tod_prod(tokens: tuple[Token, ...]) -> Token | None:
    a = tokens[0]
    b = tokens[-1]
    if a.dim != "time" or b.dim != "time":
        return None
    rt_a: RelTime = a.value
    rt_b: RelTime = b.value
    # Compose: take day from rt_a, time-of-day from rt_b.


    def go(ref: dt.datetime):
        v_a = rt_a.compute(ref)
        v_b = rt_b.compute(ref)
        if not isinstance(v_a, InstantValue) or not isinstance(v_b, InstantValue):
            return None
        new_value = v_a.value.replace(
            hour=v_b.value.hour,
            minute=v_b.value.minute,
            second=v_b.value.second,
        )
        return InstantValue(value=new_value, grain=v_b.grain)

    return _tt(
        RelTime(
            compute=go,
            grain=rt_b.grain,
            key=("time_at_tod", rt_a.key, rt_b.key),
        )
    )


_time_at_tod_rule = Rule(
    name="<time> at <tod>",
    pattern=(
        predicate(_is_day_grain, "is_day"),
        regex(r"at|@"),
        predicate(_is_hour_or_minute, "is_tod"),
    ),
    prod=_time_at_tod_prod,
)


# bare "<time> <tod>" e.g. "tomorrow 5pm"
_time_tod_juxtapose_rule = Rule(
    name="<time> <tod>",
    pattern=(
        predicate(_is_day_grain, "is_day"),
        predicate(_is_hour_or_minute, "is_tod"),
    ),
    prod=_time_at_tod_prod,
)


def _tod_on_day_prod(tokens: tuple[Token, ...]) -> Token | None:
    """e.g. 'at 9am on Saturday' — TOD followed by 'on'/'this' + day."""
    tod_tok = tokens[0]
    day_tok = tokens[-1]
    if not _is_hour_or_minute(tod_tok) or not _is_day_grain(day_tok):
        return None
    rt_a = day_tok.value
    rt_b = tod_tok.value


    def go(ref: dt.datetime):
        v_a = rt_a.compute(ref)
        v_b = rt_b.compute(ref)
        if not isinstance(v_a, InstantValue) or not isinstance(v_b, InstantValue):
            return None
        new_value = v_a.value.replace(
            hour=v_b.value.hour,
            minute=v_b.value.minute,
            second=v_b.value.second,
        )
        return InstantValue(value=new_value, grain=v_b.grain)

    return _tt(
        RelTime(
            compute=go,
            grain=rt_b.grain,
            key=("tod_on_day", rt_a.key, rt_b.key),
        )
    )


_tod_on_day_rule = Rule(
    name="<tod> on <day>",
    pattern=(
        predicate(_is_hour_or_minute, "is_tod"),
        regex(r"on|this"),
        predicate(_is_day_grain, "is_day"),
    ),
    prod=_tod_on_day_prod,
)


_tod_day_juxtapose_rule = Rule(
    name="<tod> <day>",
    pattern=(
        predicate(_is_hour_or_minute, "is_tod"),
        predicate(_is_day_grain, "is_day"),
    ),
    prod=_tod_on_day_prod,
)


# ---------------------------------------------------------------------------
# Aggregate


def _absorb_on_prod(tokens: tuple[Token, ...]) -> Token | None:
    return tokens[1]


_absorb_on_rule = Rule(
    name="on <day>",
    pattern=(regex(r"on"), predicate(_is_day_grain, "is_day")),
    prod=_absorb_on_prod,
)

_absorb_in_month_rule = Rule(
    name="in <month>",
    pattern=(regex(r"in|during"), predicate(_is_month_grain, "is_month")),
    prod=_absorb_on_prod,
)

_absorb_in_year_rule = Rule(
    name="in <year>",
    pattern=(regex(r"in|during"), predicate(_is_year_grain, "is_year")),
    prod=_absorb_on_prod,
)


# ---------------------------------------------------------------------------
# Final rule list


_BASE_RULES: tuple[Rule, ...] = (
    *_instants_rules(),
    *_all_named_rules(),
    _year_in_adbc_rule,
    _year_in_rule,
    _year_adbc_rule,
    _yyyymmdd_rule,
    _mm_dd_yyyy_rule,
    _mm_dd_rule,
    _mm_yyyy_rule,
    _yyyy_mm_rule,
    _month_year_rule,
    _the_dom_rule,
    _month_dom_numeric_rule,
    _month_dom_ordinal_rule,
    _month_dom_regex_rule,
    _dom_of_month_numeral_rule,
    _dom_of_month_ordinal_rule,
    _dom_regex_of_month_rule,
    _dom_regex_month_rule,
    _month_dom_regex_extra_rule,
    _month_the_dom_regex_rule,
    _the_dom_regex_of_month_rule,
    _the_dom_of_month_ord_rule,
    _the_dom_of_month_num_rule,
    _dom_month_year_rule,
    _month_dom_year_rule,
    _month_dom_regex_year_rule,
    _dom_regex_month_year_rule,
    _cycle_rule,
    _next_dow_rule,
    _hhmmss_rule,
    _hhmm_rule,
    _hhmm_ampm_rule,
    _bare_hour_ampm_rule,
    _hour_oclock_rule,
    _word_hour_ampm_rule,
    _word_hour_oclock_rule,
    _bare_word_hour_rule,
    _at_tod_rule,
    _noon_midnight_rule,
    _half_past_rule,
    _quarter_past_rule,
    _quarter_to_rule,
    _half_to_rule,
    _n_past_hour_rule,
    _n_to_hour_rule,
    _bare_n_past_hour_rule,
    _bare_n_to_hour_rule,
    _morning_rule,
    _afternoon_rule,
    _evening_rule,
    _night_rule,
    _tonight_rule,
    _this_part_of_day_rule,
    _last_night_rule,
    _weekend_rule,
    _the_week_rule,
    _in_a_grain_rule,
    _in_n_grain_rule,
    _n_grain_from_now_rule,
    _n_grain_ago_rule,
    _a_grain_ago_rule,
    _in_digits_grain_rule,
    _digits_grain_ago_rule,
    _digits_grain_from_now_rule,
    _n_dow_from_now_rule,
    _n_dow_ago_rule,
    _between_and_rule,
    _from_to_rule,
    _interval_dash_rule,
    _until_rule,
    _since_rule,
    _time_at_tod_rule,
    _time_tod_juxtapose_rule,
    _tod_on_day_rule,
    _tod_day_juxtapose_rule,
    _absorb_on_rule,
    _absorb_in_month_rule,
    _absorb_in_year_rule,
    *_holidays_rules(),
)


RULES: tuple[Rule, ...] = _BASE_RULES
