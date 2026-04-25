"""Supplemental English Time rules: relative + cycle expressions.

This module is auto-discovered by the puckling registry as a `*_rules.py`
sibling of `rules.py`. It adds coverage for patterns the foundation rules
do not yet emit:

- `the next/last/past <n> <grain>` (interval form: "the next 3 days")
- `<n>-th <weekday> of <month>` (e.g. "the third Monday of October")
- `the <ord> of next/last week|month|year` (e.g. "the 5th of next month")
- `every <weekday>` / `every day`
- `<day> <part-of-day>` for explicit day+POD intervals (tomorrow morning,
  yesterday evening, this morning) — produced as concrete intervals so callers
  can read `from`/`to` instants
- `early <part-of-day>` / `late <part-of-day>` (narrower POD intervals)
- `the <weekday> after next`, `the next/last <weekday>`,
  `the <ord> <weekday> from now`

Hard or context-sensitive cases are marked `# TODO(puckling): edge case`.
"""

from __future__ import annotations

import datetime as dt

from puckling.dimensions.time.en._helpers import (
    RelTime,
    day_of_week_relative,
    get_int_value,
    last_day_of_week,
    next_day_of_week,
)
from puckling.dimensions.time.grain import Grain, add_grain, truncate
from puckling.dimensions.time.types import (
    InstantValue,
    IntervalValue,
)
from puckling.predicates import is_numeral, is_ordinal
from puckling.types import RegexMatch, Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Shared maps and small helpers
# ---------------------------------------------------------------------------

_CYCLE_GRAINS: dict[str, Grain] = {
    "second": Grain.SECOND,
    "minute": Grain.MINUTE,
    "hour": Grain.HOUR,
    "day": Grain.DAY,
    "week": Grain.WEEK,
    "month": Grain.MONTH,
    "quarter": Grain.QUARTER,
    "year": Grain.YEAR,
}

_WORD_NUMS: dict[str, int] = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12,
}

_WEEKDAY_TABLE: tuple[tuple[str, int], ...] = (
    ("monday", 0), ("mon", 0),
    ("tuesday", 1), ("tues", 1), ("tue", 1),
    ("wednesday", 2), ("wednes", 2), ("wed", 2),
    ("thursday", 3), ("thurs", 3), ("thur", 3), ("thu", 3),
    ("friday", 4), ("fri", 4),
    ("saturday", 5), ("sat", 5),
    ("sunday", 6), ("sun", 6),
)

_WEEKDAY_PATTERN = (
    r"mondays?|mon\.?"
    r"|tuesdays?|tues?\.?"
    r"|wed?nesdays?|wed\.?"
    r"|thursdays?|thu(?:rs?)?\.?"
    r"|fridays?|fri\.?"
    r"|saturdays?|sat\.?"
    r"|sundays?|sun\.?"
)

_MONTH_TABLE: tuple[tuple[str, int], ...] = (
    ("january", 1), ("jan", 1),
    ("february", 2), ("feb", 2),
    ("march", 3), ("mar", 3),
    ("april", 4), ("apr", 4),
    ("may", 5),
    ("june", 6), ("jun", 6),
    ("july", 7), ("jul", 7),
    ("august", 8), ("aug", 8),
    ("september", 9), ("sept", 9), ("sep", 9),
    ("october", 10), ("oct", 10),
    ("november", 11), ("nov", 11),
    ("december", 12), ("dec", 12),
)

_MONTH_PATTERN = (
    r"january|jan\.?|february|feb\.?|march|mar\.?|april|apr\.?|may"
    r"|june|jun\.?|july|jul\.?|august|aug\.?"
    r"|september|sept?\.?|october|oct\.?|november|nov\.?|december|dec\.?"
)

_ORDINAL_WORDS: dict[str, int] = {
    "first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3,
    "fourth": 4, "4th": 4, "fifth": 5, "5th": 5, "sixth": 6, "6th": 6,
    "seventh": 7, "7th": 7, "eighth": 8, "8th": 8, "ninth": 9, "9th": 9,
    "tenth": 10, "10th": 10,
}

_NTH_OCC_PATTERN = r"first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th"

_GRAIN_PATTERN = (
    r"seconds?|minutes?|hours?|days?|weeks?|months?|quarters?|years?"
)

_FORWARD_DIRS = ("next", "coming", "following", "upcoming")
_BACKWARD_DIRS = ("last", "past", "previous")
_THIS_DIRS = ("this", "current")
_DIR_PATTERN = r"next|last|past|previous|coming|following|upcoming"
_DIR_PATTERN_WITH_THIS = r"next|last|past|previous|this|current|coming|following|upcoming"


def _tt(value: RelTime) -> Token:
    return Token(dim="time", value=value)


def _parse_int_word(text: str) -> int | None:
    text = text.strip().lower()
    if text in _WORD_NUMS:
        return _WORD_NUMS[text]
    if text.isdigit():
        return int(text)
    return None


def _parse_ord_word(text: str) -> int | None:
    text = text.strip().lower()
    if text in _ORDINAL_WORDS:
        return _ORDINAL_WORDS[text]
    digits = text.rstrip("stndrh.")
    if digits.isdigit():
        return int(digits)
    return None


def _ord_value(tok: Token) -> int | None:
    """Pull an ordinal int from an ordinal token or an ordinal-shaped regex match."""
    if tok.dim == "ordinal":
        v = getattr(tok.value, "value", None)
        return v if isinstance(v, int) else None
    if isinstance(tok.value, RegexMatch):
        return _parse_ord_word(tok.value.text)
    return None


def _direction_offset(text: str) -> int | None:
    text = text.lower()
    if text in _FORWARD_DIRS:
        return 1
    if text in _BACKWARD_DIRS:
        return -1
    if text in _THIS_DIRS:
        return 0
    return None


def _grain_from_match(text: str) -> Grain | None:
    return _CYCLE_GRAINS.get(text.lower().rstrip("s"))


def _weekday_from_match(text: str) -> int | None:
    """Resolve a weekday regex match (e.g. 'Mondays', 'Tue.') to 0..6."""
    key = text.lower().rstrip("s.").rstrip(".")
    for prefix, wd in _WEEKDAY_TABLE:
        if key == prefix or key.startswith(prefix):
            return wd
    return None


def _month_from_match(text: str) -> int | None:
    key = text.lower().rstrip(".")
    for prefix, m in _MONTH_TABLE:
        if key == prefix or key.startswith(prefix):
            return m
    return None


def _is_named_dow(t: Token) -> bool:
    """Match RelTime tokens produced by `day_of_week_relative` (a weekday name)."""
    if t.dim != "time":
        return False
    rt = t.value
    if not hasattr(rt, "key"):
        return False
    return bool(rt.key) and rt.key[0] == "dow_rel"


def _value_grain(t: Token) -> Grain | None:
    return getattr(t.value, "grain", None)


def _is_part_of_day(t: Token) -> bool:
    """A RelTime that resolves to a part-of-day interval (morning/afternoon/...)."""
    if t.dim != "time":
        return False
    rt = t.value
    if not hasattr(rt, "key"):
        return False
    return bool(rt.key) and rt.key[0] == "pod_interval"


def _is_day_grain(t: Token) -> bool:
    return t.dim == "time" and _value_grain(t) is Grain.DAY


def _named_dow_weekday(t: Token) -> int | None:
    """Pull the weekday index out of a `_is_named_dow` token's key."""
    rt = t.value
    return rt.key[1] if len(rt.key) > 1 else None


def _next_dow_target(ref: dt.datetime, weekday: int, *, week_offset: int = 0) -> dt.datetime:
    """The next strict future occurrence of `weekday`, optionally offset N weeks."""
    ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
    delta = (weekday - ref_day.weekday()) % 7
    if delta == 0:
        delta = 7
    return ref_day + dt.timedelta(days=delta + 7 * week_offset)


# ---------------------------------------------------------------------------
# "the next/last/past <n> <grain>"  →  closed interval
# ---------------------------------------------------------------------------


def _next_n_grain_interval(n: int, grain: Grain, *, future: bool) -> RelTime:
    """[today, today + n*grain) for future; [today - n*grain, today) for past.

    Mirrors Duckling's `cycleN` semantics for "the next/last N <grain>" — the
    interval is anchored at the start of the current period (truncated).
    """

    def go(ref: dt.datetime):
        anchor = truncate(ref, grain)
        if future:
            start_v, end_v = anchor, add_grain(anchor, grain, n)
        else:
            start_v, end_v = add_grain(anchor, grain, -n), anchor
        return IntervalValue(
            start=InstantValue(value=start_v, grain=grain),
            end=InstantValue(value=end_v, grain=grain),
        )

    return RelTime(
        compute=go,
        grain=grain,
        key=("next_n_grain_interval", grain.value, n, future),
    )


def _build_n_grain_token(direction_text: str, n: int | None, grain: Grain | None) -> Token | None:
    if n is None or n <= 0 or grain is None:
        return None
    future = direction_text.lower() in _FORWARD_DIRS
    return _tt(_next_n_grain_interval(n, grain, future=future))


def _the_n_grain_prod(tokens: tuple[Token, ...]) -> Token | None:
    """`the next 3 days` — direction at index 1, numeral at index 2, grain at 3."""
    direction = tokens[1].value
    grain_match = tokens[3].value
    if not isinstance(direction, RegexMatch) or not isinstance(grain_match, RegexMatch):
        return None
    n = get_int_value(tokens[2].value) if is_numeral(tokens[2]) else None
    return _build_n_grain_token(direction.text, n, _grain_from_match(grain_match.text))


def _the_digits_grain_prod(tokens: tuple[Token, ...]) -> Token | None:
    """`the next 3 days` with a regex-numeral path (digits or word-num)."""
    direction = tokens[1].value
    digits = tokens[2].value
    grain_match = tokens[3].value
    if not (
        isinstance(direction, RegexMatch)
        and isinstance(digits, RegexMatch)
        and isinstance(grain_match, RegexMatch)
    ):
        return None
    return _build_n_grain_token(
        direction.text, _parse_int_word(digits.text), _grain_from_match(grain_match.text)
    )


def _bare_n_grain_prod(tokens: tuple[Token, ...]) -> Token | None:
    direction = tokens[0].value
    grain_match = tokens[2].value
    if not isinstance(direction, RegexMatch) or not isinstance(grain_match, RegexMatch):
        return None
    n = get_int_value(tokens[1].value) if is_numeral(tokens[1]) else None
    return _build_n_grain_token(direction.text, n, _grain_from_match(grain_match.text))


def _bare_digits_grain_prod(tokens: tuple[Token, ...]) -> Token | None:
    direction = tokens[0].value
    digits = tokens[1].value
    grain_match = tokens[2].value
    if not (
        isinstance(direction, RegexMatch)
        and isinstance(digits, RegexMatch)
        and isinstance(grain_match, RegexMatch)
    ):
        return None
    return _build_n_grain_token(
        direction.text, _parse_int_word(digits.text), _grain_from_match(grain_match.text)
    )


_DIGITS_OR_WORDNUM_PATTERN = r"\d+|" + "|".join(_WORD_NUMS.keys())

_the_n_grain_rule = Rule(
    name="the next/last/past <n> <grain>",
    pattern=(
        regex(r"the|these|those"),
        regex(_DIR_PATTERN),
        predicate(is_numeral, "is_n"),
        regex(_GRAIN_PATTERN),
    ),
    prod=_the_n_grain_prod,
)

_the_digits_grain_rule = Rule(
    name="the next/last/past <digits> <grain>",
    pattern=(
        regex(r"the|these|those"),
        regex(_DIR_PATTERN),
        regex(_DIGITS_OR_WORDNUM_PATTERN),
        regex(_GRAIN_PATTERN),
    ),
    prod=_the_digits_grain_prod,
)

_bare_n_grain_rule = Rule(
    name="next/last/past <n> <grain>",
    pattern=(
        regex(_DIR_PATTERN),
        predicate(is_numeral, "is_n"),
        regex(_GRAIN_PATTERN),
    ),
    prod=_bare_n_grain_prod,
)

_bare_digits_grain_rule = Rule(
    name="next/last/past <digits> <grain>",
    pattern=(
        regex(_DIR_PATTERN),
        regex(_DIGITS_OR_WORDNUM_PATTERN),
        regex(_GRAIN_PATTERN),
    ),
    prod=_bare_digits_grain_prod,
)


# ---------------------------------------------------------------------------
# "<n>-th <weekday> of <month>"  e.g. "the third Monday of October"
# ---------------------------------------------------------------------------


def _nth_dow_of_named_month(n: int, weekday: int, month: int) -> RelTime:
    """The n-th occurrence of `weekday` in `month` — picks the nearest future year."""

    def go(ref: dt.datetime):
        ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
        for year_offset in (0, 1):
            year = ref.year + year_offset
            first = dt.date(year, month, 1)
            offset = (weekday - first.weekday()) % 7
            day = 1 + offset + 7 * (n - 1)
            try:
                target = dt.datetime(year, month, day, tzinfo=ref.tzinfo)
            except ValueError:
                continue
            if target >= ref_day:
                return InstantValue(value=target, grain=Grain.DAY)
        return None

    return RelTime(
        compute=go,
        grain=Grain.DAY,
        key=("nth_dow_of_month", n, weekday, month),
    )


def _nth_dow_of_month_prod_with_the(tokens: tuple[Token, ...]) -> Token | None:
    """`the <ord> <weekday> of <month>` — single regex-driven rule."""
    return _nth_dow_of_month_from_matches(
        tokens[1].value, tokens[2].value, tokens[4].value
    )


def _nth_dow_of_month_prod_no_the(tokens: tuple[Token, ...]) -> Token | None:
    """`<ord> <weekday> of <month>` (without leading 'the')."""
    return _nth_dow_of_month_from_matches(
        tokens[0].value, tokens[1].value, tokens[3].value
    )


def _nth_dow_of_month_from_matches(
    ord_match: object, dow_match: object, month_match: object
) -> Token | None:
    if not (
        isinstance(ord_match, RegexMatch)
        and isinstance(dow_match, RegexMatch)
        and isinstance(month_match, RegexMatch)
    ):
        return None
    n = _parse_ord_word(ord_match.text)
    weekday = _weekday_from_match(dow_match.text)
    month = _month_from_match(month_match.text)
    if n is None or weekday is None or month is None:
        return None
    return _tt(_nth_dow_of_named_month(n, weekday, month))


_nth_dow_of_month_the_rule = Rule(
    name="the <ord> <weekday> of <month>",
    pattern=(
        regex(r"the"),
        regex(_NTH_OCC_PATTERN),
        regex(_WEEKDAY_PATTERN),
        regex(r"of|in"),
        regex(_MONTH_PATTERN),
    ),
    prod=_nth_dow_of_month_prod_with_the,
)

_nth_dow_of_month_bare_rule = Rule(
    name="<ord> <weekday> of <month>",
    pattern=(
        regex(_NTH_OCC_PATTERN),
        regex(_WEEKDAY_PATTERN),
        regex(r"of|in"),
        regex(_MONTH_PATTERN),
    ),
    prod=_nth_dow_of_month_prod_no_the,
)


# ---------------------------------------------------------------------------
# "the <ord> of next/last week|month|year"
# ---------------------------------------------------------------------------


def _nth_of_cycle(n: int, grain: Grain, offset: int) -> RelTime:
    """The n-th day of the (offset)-th period at `grain`.

    For grain in {WEEK, MONTH, YEAR}: take the period that is `offset` away
    from the current one and return its first day + (n-1) days. The result is
    rejected if it would fall outside the period (e.g. `the 32nd of next month`).
    """

    def go(ref: dt.datetime):
        anchor = truncate(ref, grain)
        period_start = add_grain(anchor, grain, offset)
        target = period_start + dt.timedelta(days=n - 1)
        if target >= add_grain(period_start, grain, 1):
            return None
        return InstantValue(value=target, grain=Grain.DAY)

    return RelTime(
        compute=go,
        grain=Grain.DAY,
        key=("nth_of_cycle", n, grain.value, offset),
    )


def _nth_of_cycle_token(
    n: int | None, direction_text: str, grain_text: str
) -> Token | None:
    if n is None or n < 1 or n > 366:
        return None
    grain = _grain_from_match(grain_text)
    if grain not in (Grain.WEEK, Grain.MONTH, Grain.YEAR):
        return None
    offset = _direction_offset(direction_text)
    if offset is None:
        return None
    return _tt(_nth_of_cycle(n, grain, offset))


def _the_ord_of_cycle_ord_prod(tokens: tuple[Token, ...]) -> Token | None:
    """`the <ord-token> of next/last <cycle>` (ord from the ordinal dimension)."""
    direction = tokens[3].value
    grain_match = tokens[4].value
    if not isinstance(direction, RegexMatch) or not isinstance(grain_match, RegexMatch):
        return None
    return _nth_of_cycle_token(_ord_value(tokens[1]), direction.text, grain_match.text)


def _the_ord_regex_of_cycle_prod(tokens: tuple[Token, ...]) -> Token | None:
    """`the <ord-regex> of next/last <cycle>` (ord parsed from a regex match)."""
    ord_match = tokens[1].value
    direction = tokens[3].value
    grain_match = tokens[4].value
    if not (
        isinstance(ord_match, RegexMatch)
        and isinstance(direction, RegexMatch)
        and isinstance(grain_match, RegexMatch)
    ):
        return None
    return _nth_of_cycle_token(
        _parse_ord_word(ord_match.text), direction.text, grain_match.text
    )


_ORD_REGEX = (
    r"(?:[12]\d|3[01]|0?[1-9])(?:st|nd|rd|th)"
    + "|"
    + "|".join(sorted(_ORDINAL_WORDS.keys(), key=len, reverse=True))
)

_the_ord_of_cycle_ord_rule = Rule(
    name="the <ord> of next/last <cycle>",
    pattern=(
        regex(r"the"),
        predicate(is_ordinal, "is_ord"),
        regex(r"of"),
        regex(_DIR_PATTERN_WITH_THIS),
        regex(r"weeks?|months?|years?"),
    ),
    prod=_the_ord_of_cycle_ord_prod,
)

_the_ord_regex_of_cycle_rule = Rule(
    name="the <ord-regex> of next/last <cycle>",
    pattern=(
        regex(r"the"),
        regex(_ORD_REGEX),
        regex(r"of"),
        regex(_DIR_PATTERN_WITH_THIS),
        regex(r"weeks?|months?|years?"),
    ),
    prod=_the_ord_regex_of_cycle_prod,
)


# ---------------------------------------------------------------------------
# "every <weekday>" / "every day"
# ---------------------------------------------------------------------------


def _every_dow_prod(tokens: tuple[Token, ...]) -> Token | None:
    """`every <weekday>` resolves to the next occurrence (recurring semantics
    live above the resolver — this surfaces the closest future instance)."""
    pat = tokens[1].value
    if not isinstance(pat, RegexMatch):
        return None
    weekday = _weekday_from_match(pat.text)
    if weekday is None:
        return None
    return _tt(day_of_week_relative(weekday))


_every_dow_rule = Rule(
    name="every <weekday>",
    pattern=(regex(r"every|each"), regex(_WEEKDAY_PATTERN)),
    prod=_every_dow_prod,
)


def _every_day_prod(_tokens: tuple[Token, ...]) -> Token | None:
    def go(ref: dt.datetime):
        return InstantValue(
            value=ref.replace(hour=0, minute=0, second=0, microsecond=0),
            grain=Grain.DAY,
        )

    # TODO(puckling): edge case — Duckling has true recurring semantics here.
    return _tt(RelTime(compute=go, grain=Grain.DAY, latent=True, key=("every_day",)))


_every_day_rule = Rule(
    name="every day",
    pattern=(regex(r"every|each"), regex(r"days?")),
    prod=_every_day_prod,
)


# ---------------------------------------------------------------------------
# "<day> <part-of-day>"  →  concrete interval on that day
# ---------------------------------------------------------------------------


def _day_at_pod(day_rt: RelTime, pod_rt: RelTime) -> RelTime:
    """Anchor a part-of-day interval to a specific day."""

    def go(ref: dt.datetime):
        v_day = day_rt.compute(ref)
        v_pod = pod_rt.compute(ref)
        if not isinstance(v_day, InstantValue) or not isinstance(v_pod, IntervalValue):
            return None
        anchor = v_pod.start.value.replace(
            year=v_day.value.year, month=v_day.value.month, day=v_day.value.day
        )
        # Compute end relative to the (start, end) delta to preserve wrap-around POD.
        delta = v_pod.end.value - v_pod.start.value
        return IntervalValue(
            start=InstantValue(value=anchor, grain=Grain.HOUR),
            end=InstantValue(value=anchor + delta, grain=Grain.HOUR),
        )

    return RelTime(
        compute=go,
        grain=Grain.HOUR,
        key=("day_at_pod", day_rt.key, pod_rt.key),
    )


def _day_pod_prod(tokens: tuple[Token, ...]) -> Token | None:
    day_tok = tokens[0]
    pod_tok = tokens[-1]
    if not _is_day_grain(day_tok) or not _is_part_of_day(pod_tok):
        return None
    return _tt(_day_at_pod(day_tok.value, pod_tok.value))


_day_pod_juxtaposed_rule = Rule(
    name="<day> <part-of-day>",
    pattern=(
        predicate(_is_day_grain, "is_day"),
        predicate(_is_part_of_day, "is_pod"),
    ),
    prod=_day_pod_prod,
)


_day_in_pod_rule = Rule(
    name="<day> in the <part-of-day>",
    pattern=(
        predicate(_is_day_grain, "is_day"),
        regex(r"in the|on"),
        predicate(_is_part_of_day, "is_pod"),
    ),
    prod=_day_pod_prod,
)


# ---------------------------------------------------------------------------
# "early <part-of-day>" / "late <part-of-day>"
# ---------------------------------------------------------------------------


def _narrow_pod(start_h: int, end_h: int, *, late: bool) -> RelTime:
    """Half-shifted part-of-day: 'early X' = first half; 'late X' = second half."""

    def go(ref: dt.datetime):
        ref_day = ref.replace(hour=0, minute=0, second=0, microsecond=0)
        wrap_end_h = end_h + 24 if end_h <= start_h else end_h
        mid = (start_h + wrap_end_h) // 2
        sh, eh = (mid, wrap_end_h) if late else (start_h, mid)
        return IntervalValue(
            start=InstantValue(value=ref_day + dt.timedelta(hours=sh), grain=Grain.HOUR),
            end=InstantValue(value=ref_day + dt.timedelta(hours=eh), grain=Grain.HOUR),
        )

    return RelTime(
        compute=go,
        grain=Grain.HOUR,
        latent=True,
        key=("narrow_pod", start_h, end_h, late),
    )


# (start_h, end_h) pairs for each part-of-day; end_h <= start_h means overnight.
_POD_BOUNDS: dict[str, tuple[int, int]] = {
    "morning": (0, 12),
    "afternoon": (12, 19),
    "evening": (18, 0),
    "night": (18, 0),
}

_POD_LOOKUP_PATTERN = r"morning|after\s?noo?n|evening|night"


def _narrow_pod_prod(tokens: tuple[Token, ...]) -> Token | None:
    """`early/late <pod>` — a single rule covers all four parts of day."""
    adj_match = tokens[0].value
    pod_match = tokens[1].value
    if not isinstance(adj_match, RegexMatch) or not isinstance(pod_match, RegexMatch):
        return None
    late = adj_match.text.lower() == "late"
    pod_key = pod_match.text.lower().replace(" ", "")
    # Normalize "afternoon" / "afterno(o?)n" variants.
    if pod_key.startswith("after"):
        pod_key = "afternoon"
    bounds = _POD_BOUNDS.get(pod_key)
    if bounds is None:
        return None
    start_h, end_h = bounds
    return _tt(_narrow_pod(start_h, end_h, late=late))


_narrow_pod_rule = Rule(
    name="early/late <part-of-day>",
    pattern=(regex(r"early|late"), regex(_POD_LOOKUP_PATTERN)),
    prod=_narrow_pod_prod,
)


# ---------------------------------------------------------------------------
# "<weekday> after next" — two weeks out from the next occurrence.
# ---------------------------------------------------------------------------


def _dow_after_next_token(weekday: int) -> Token:
    def go(ref: dt.datetime):
        return InstantValue(value=_next_dow_target(ref, weekday, week_offset=1), grain=Grain.DAY)

    return _tt(RelTime(compute=go, grain=Grain.DAY, key=("dow_after_next", weekday)))


def _weekday_after_next_prod(tokens: tuple[Token, ...]) -> Token | None:
    """`monday after next` (no leading 'the')."""
    dow_tok = tokens[0]
    if not _is_named_dow(dow_tok):
        return None
    weekday = _named_dow_weekday(dow_tok)
    if weekday is None:
        return None
    return _dow_after_next_token(weekday)


def _the_weekday_after_next_prod(tokens: tuple[Token, ...]) -> Token | None:
    """`the monday after next`."""
    dow_tok = tokens[1]
    if not _is_named_dow(dow_tok):
        return None
    weekday = _named_dow_weekday(dow_tok)
    if weekday is None:
        return None
    return _dow_after_next_token(weekday)


_weekday_after_next_rule = Rule(
    name="<weekday> after next",
    pattern=(
        predicate(_is_named_dow, "is_named_dow"),
        regex(r"after"),
        regex(r"next"),
    ),
    prod=_weekday_after_next_prod,
)


_the_weekday_after_next_rule = Rule(
    name="the <weekday> after next",
    pattern=(
        regex(r"the"),
        predicate(_is_named_dow, "is_named_dow"),
        regex(r"after"),
        regex(r"next"),
    ),
    prod=_the_weekday_after_next_prod,
)


# ---------------------------------------------------------------------------
# "the <ord> <weekday> from now"
# ---------------------------------------------------------------------------


def _ord_dow_from_now_prod(tokens: tuple[Token, ...]) -> Token | None:
    n = _ord_value(tokens[1])
    dow_tok = tokens[2]
    if n is None or n < 1 or not _is_named_dow(dow_tok):
        return None
    weekday = _named_dow_weekday(dow_tok)
    if weekday is None:
        return None

    def go(ref: dt.datetime):
        return InstantValue(
            value=_next_dow_target(ref, weekday, week_offset=n - 1),
            grain=Grain.DAY,
        )

    return _tt(RelTime(compute=go, grain=Grain.DAY, key=("ord_dow_from_now", n, weekday)))


_the_ord_dow_from_now_rule = Rule(
    name="the <ord> <weekday> from now",
    pattern=(
        regex(r"the"),
        predicate(is_ordinal, "is_ord"),
        predicate(_is_named_dow, "is_named_dow"),
        regex(r"from now|hence"),
    ),
    prod=_ord_dow_from_now_prod,
)


# ---------------------------------------------------------------------------
# "the next/last <weekday>" — extends the foundation's "next/last <weekday>".
# ---------------------------------------------------------------------------


def _the_next_last_dow_prod(tokens: tuple[Token, ...]) -> Token | None:
    direction_match = tokens[1].value
    dow_tok = tokens[2]
    if not isinstance(direction_match, RegexMatch) or not _is_named_dow(dow_tok):
        return None
    weekday = _named_dow_weekday(dow_tok)
    if weekday is None:
        return None
    direction = direction_match.text.lower()
    if direction in _FORWARD_DIRS:
        return _tt(next_day_of_week(weekday))
    if direction in _BACKWARD_DIRS:
        return _tt(last_day_of_week(weekday))
    return None


_the_next_last_dow_rule = Rule(
    name="the next/last <weekday>",
    pattern=(
        regex(r"the"),
        regex(_DIR_PATTERN),
        predicate(_is_named_dow, "is_named_dow"),
    ),
    prod=_the_next_last_dow_prod,
)


# ---------------------------------------------------------------------------
# Final aggregate
# ---------------------------------------------------------------------------


RULES: tuple[Rule, ...] = (
    _the_n_grain_rule,
    _the_digits_grain_rule,
    _bare_n_grain_rule,
    _bare_digits_grain_rule,
    _nth_dow_of_month_the_rule,
    _nth_dow_of_month_bare_rule,
    _the_ord_of_cycle_ord_rule,
    _the_ord_regex_of_cycle_rule,
    _every_dow_rule,
    _every_day_rule,
    _day_pod_juxtaposed_rule,
    _day_in_pod_rule,
    _narrow_pod_rule,
    _weekday_after_next_rule,
    _the_weekday_after_next_rule,
    _the_ord_dow_from_now_rule,
    _the_next_last_dow_rule,
)
