"""Supplemental English Time interval rules.

The foundation `time/en/rules.py` already covers the core interval cases
("between X and Y", "from X to Y", "<X> - <Y>", "until/before X",
"since/after/from X"). This module adds productions that close gaps in
upstream Duckling's `Duckling/Time/EN/Rules.hs`:

- `by <time>` — open interval bounded above by `<time>` (Duckling's
  `ruleIntervalBy`).
- `<year>-<year>` / `<year> to <year>` and `from <year> to <year>` —
  latent year-range intervals (Duckling's `ruleIntervalYearLatent`).
- `<month> <dom> to <dom>` and `from <month> <dom> to <dom>` —
  same-month day intervals (Duckling's `ruleIntervalMonthDDDD` and
  `ruleIntervalFromMonthDDDD`).
- `<dom> to <dom> [of] <month>` and the `from`/`the` variants —
  Duckling's `ruleIntervalDDDDMonth`, `ruleIntervalFromDDDDMonth`,
  and `ruleIntervalFromDDDDOfMonth`.

Day-of-month and year endpoints come both as predicate-matched tokens
(numerals/ordinals when the numeral dimension is loaded) and as regex
captures (so the rules also fire under `dims=("time",)`, where numeral
rules are absent — mirroring how the foundation's date rules already
fall back to raw digit regexes).
"""

from __future__ import annotations

from puckling.dimensions.time.en._helpers import (
    RelTime,
    fixed_year,
    get_int_value,
    interval,
    open_interval,
    with_day_of_month,
)
from puckling.dimensions.time.grain import Grain
from puckling.dimensions.time.types import IntervalDirection
from puckling.predicates import is_time
from puckling.types import RegexMatch, Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Shared regex fragments


# Both the year-range and the day-range patterns accept the same separators
# (`-`, `to`, `thru`/`through`, `until`/`till`).
_RANGE_SEP = r"\-|to|th?ru|through|(?:un)?til(?:l)?"

# Day-of-month regex (mirrors the foundation's `_DOM_REGEX` shape, kept
# self-contained so we don't depend on internal symbols of `rules.py`).
_DOM_REGEX = r"(?:[12]\d|3[01]|0?[1-9])(?:st|nd|rd|th)?"

_YEAR_REGEX = r"\d{4}"

_OF_OR_IN = r"of|in"

# `from( the)?` / `to( the)?` — Duckling's optional "the" articles.
_FROM_OPT_THE = r"from(?:\s+the)?"
_SEP_OPT_THE = rf"(?:{_RANGE_SEP})(?:\s+the)?"


# ---------------------------------------------------------------------------
# Token helpers


def _tt(value: RelTime) -> Token:
    return Token(dim="time", value=value)


def _is_month(t: Token) -> bool:
    return t.dim == "time" and getattr(t.value, "grain", None) is Grain.MONTH


def _dom_from_token(t: Token) -> int | None:
    """Extract a 1..31 day-of-month value from numeral / ordinal / regex tokens."""
    if t.dim == "ordinal":
        v = getattr(t.value, "value", None)
        if isinstance(v, int) and 1 <= v <= 31:
            return v
    if t.dim == "numeral":
        v = get_int_value(t.value)
        if v is not None and 1 <= v <= 31:
            return v
    if t.dim == "regex_match" and isinstance(t.value, RegexMatch):
        try:
            n = int(t.value.text.lower().strip().rstrip("stndrh."))
        except ValueError:
            return None
        if 1 <= n <= 31:
            return n
    return None


def _is_dom_token(t: Token) -> bool:
    return _dom_from_token(t) is not None


def _year_from_regex_token(t: Token, *, lo: int = 1000, hi: int = 9999) -> int | None:
    if t.dim != "regex_match" or not isinstance(t.value, RegexMatch):
        return None
    try:
        n = int(t.value.text)
    except ValueError:
        return None
    return n if lo <= n <= hi else None


# ---------------------------------------------------------------------------
# Productions — one per family, position-agnostic so any rule with the right
# slot kinds (regex separators + month/dom/year tokens) can share them.


def _make_year_interval(tokens: tuple[Token, ...]) -> Token | None:
    """Find the two regex-matched 4-digit years and emit a closed interval."""
    years: list[int] = []
    for t in tokens:
        y = _year_from_regex_token(t)
        if y is not None:
            years.append(y)
    if len(years) != 2 or years[0] >= years[1]:
        return None
    return _tt(interval(fixed_year(years[0]), fixed_year(years[1])))


def _make_month_dom_interval(tokens: tuple[Token, ...]) -> Token | None:
    """Find a month token and two day-of-month values; emit a closed interval.

    Works for every variant in this file because we identify slots by token
    kind rather than by position. Reversed pairs (n1 >= n2) are rejected,
    matching Duckling's behavior.
    """
    month_tok: Token | None = None
    doms: list[int] = []
    for t in tokens:
        if _is_month(t):
            month_tok = t
            continue
        n = _dom_from_token(t)
        if n is not None:
            doms.append(n)
    if month_tok is None or len(doms) != 2 or doms[0] >= doms[1]:
        return None
    rt: RelTime = month_tok.value
    return _tt(interval(with_day_of_month(rt, doms[0]), with_day_of_month(rt, doms[1])))


# ---------------------------------------------------------------------------
# `by <time>` — open interval (BEFORE).


def _by_time_prod(tokens: tuple[Token, ...]) -> Token | None:
    inner = tokens[1]
    if inner.dim != "time":
        return None
    return _tt(open_interval(inner.value, IntervalDirection.BEFORE))


# TODO(puckling): edge case — "by the end of <time>" should resolve to a
# closed interval [now, end_of_time) rather than just BEFORE end_of_time.
_by_rule = Rule(
    name="by <time>",
    pattern=(regex(r"by"), predicate(is_time, "is_time")),
    prod=_by_time_prod,
)


# ---------------------------------------------------------------------------
# Latent year-range intervals: "2014-2016", "2014 to 2016", "1960 - 1961".

_year_year_interval_rule = Rule(
    name="<year> - <year> (interval, latent)",
    pattern=(regex(_YEAR_REGEX), regex(_RANGE_SEP), regex(_YEAR_REGEX)),
    prod=_make_year_interval,
)

_from_year_to_year_rule = Rule(
    name="from <year> to <year> (interval)",
    pattern=(
        regex(r"from"),
        regex(_YEAR_REGEX),
        regex(_RANGE_SEP),
        regex(_YEAR_REGEX),
    ),
    prod=_make_year_interval,
)

_between_year_and_year_rule = Rule(
    name="between <year> and <year> (interval)",
    pattern=(regex(r"between"), regex(_YEAR_REGEX), regex(r"and"), regex(_YEAR_REGEX)),
    prod=_make_year_interval,
)


# ---------------------------------------------------------------------------
# "<month> <dom> to <dom>" and "from <month> <dom> to <dom>".

_month_dom_to_dom_rule = Rule(
    name="<month> <dom> to <dom>",
    pattern=(
        predicate(_is_month, "is_month"),
        predicate(_is_dom_token, "is_dom"),
        regex(_RANGE_SEP),
        predicate(_is_dom_token, "is_dom"),
    ),
    prod=_make_month_dom_interval,
)

_from_month_dom_to_dom_rule = Rule(
    name="from <month> <dom> to <dom>",
    pattern=(
        regex(r"from"),
        predicate(_is_month, "is_month"),
        predicate(_is_dom_token, "is_dom"),
        regex(_RANGE_SEP),
        predicate(_is_dom_token, "is_dom"),
    ),
    prod=_make_month_dom_interval,
)

# Regex-slot variants — fire even when the parser is invoked with
# `dims=("time",)` (which excludes the numeral dimension's tokens).
_month_dom_regex_to_dom_regex_rule = Rule(
    name="<month> <dom-regex> to <dom-regex>",
    pattern=(
        predicate(_is_month, "is_month"),
        regex(_DOM_REGEX),
        regex(_RANGE_SEP),
        regex(_DOM_REGEX),
    ),
    prod=_make_month_dom_interval,
)

_from_month_dom_regex_to_dom_regex_rule = Rule(
    name="from <month> <dom-regex> to <dom-regex>",
    pattern=(
        regex(r"from"),
        predicate(_is_month, "is_month"),
        regex(_DOM_REGEX),
        regex(_RANGE_SEP),
        regex(_DOM_REGEX),
    ),
    prod=_make_month_dom_interval,
)


# ---------------------------------------------------------------------------
# "<dom> to <dom> <month>" and "<dom> to <dom> of <month>", plus the
# `from`/`the` prefixed variants — Duckling's `ruleIntervalDDDDMonth`,
# `ruleIntervalFromDDDDMonth`, `ruleIntervalFromDDDDOfMonth`.

_dom_to_dom_month_rule = Rule(
    name="<dom> to <dom> <month>",
    pattern=(
        predicate(_is_dom_token, "is_dom"),
        regex(_RANGE_SEP),
        predicate(_is_dom_token, "is_dom"),
        predicate(_is_month, "is_month"),
    ),
    prod=_make_month_dom_interval,
)

_dom_to_dom_of_month_rule = Rule(
    name="<dom> to <dom> of <month>",
    pattern=(
        predicate(_is_dom_token, "is_dom"),
        regex(_RANGE_SEP),
        predicate(_is_dom_token, "is_dom"),
        regex(_OF_OR_IN),
        predicate(_is_month, "is_month"),
    ),
    prod=_make_month_dom_interval,
)

_dom_regex_to_dom_regex_month_rule = Rule(
    name="<dom-regex> to <dom-regex> <month>",
    pattern=(
        regex(_DOM_REGEX),
        regex(_RANGE_SEP),
        regex(_DOM_REGEX),
        predicate(_is_month, "is_month"),
    ),
    prod=_make_month_dom_interval,
)

_dom_regex_to_dom_regex_of_month_rule = Rule(
    name="<dom-regex> to <dom-regex> of <month>",
    pattern=(
        regex(_DOM_REGEX),
        regex(_RANGE_SEP),
        regex(_DOM_REGEX),
        regex(_OF_OR_IN),
        predicate(_is_month, "is_month"),
    ),
    prod=_make_month_dom_interval,
)

_from_dom_to_dom_month_rule = Rule(
    name="from <dom> to <dom> <month>",
    pattern=(
        regex(_FROM_OPT_THE),
        predicate(_is_dom_token, "is_dom"),
        regex(_SEP_OPT_THE),
        predicate(_is_dom_token, "is_dom"),
        predicate(_is_month, "is_month"),
    ),
    prod=_make_month_dom_interval,
)

_from_dom_to_dom_of_month_rule = Rule(
    name="from <dom> to <dom> of <month>",
    pattern=(
        regex(_FROM_OPT_THE),
        predicate(_is_dom_token, "is_dom"),
        regex(_SEP_OPT_THE),
        predicate(_is_dom_token, "is_dom"),
        regex(_OF_OR_IN),
        predicate(_is_month, "is_month"),
    ),
    prod=_make_month_dom_interval,
)

_from_dom_regex_to_dom_regex_month_rule = Rule(
    name="from <dom-regex> to <dom-regex> <month>",
    pattern=(
        regex(_FROM_OPT_THE),
        regex(_DOM_REGEX),
        regex(_SEP_OPT_THE),
        regex(_DOM_REGEX),
        predicate(_is_month, "is_month"),
    ),
    prod=_make_month_dom_interval,
)

_from_dom_regex_to_dom_regex_of_month_rule = Rule(
    name="from <dom-regex> to <dom-regex> of <month>",
    pattern=(
        regex(_FROM_OPT_THE),
        regex(_DOM_REGEX),
        regex(_SEP_OPT_THE),
        regex(_DOM_REGEX),
        regex(_OF_OR_IN),
        predicate(_is_month, "is_month"),
    ),
    prod=_make_month_dom_interval,
)

# Explicit "the <dom> to the <dom> of <month>" — Duckling's `from( the)?`
# threading without the leading `from`.
_the_dom_to_the_dom_of_month_rule = Rule(
    name="the <dom> to the <dom> of <month>",
    pattern=(
        regex(r"the"),
        predicate(_is_dom_token, "is_dom"),
        regex(_SEP_OPT_THE),
        predicate(_is_dom_token, "is_dom"),
        regex(_OF_OR_IN),
        predicate(_is_month, "is_month"),
    ),
    prod=_make_month_dom_interval,
)

_the_dom_regex_to_the_dom_regex_of_month_rule = Rule(
    name="the <dom-regex> to the <dom-regex> of <month>",
    pattern=(
        regex(r"the"),
        regex(_DOM_REGEX),
        regex(_SEP_OPT_THE),
        regex(_DOM_REGEX),
        regex(_OF_OR_IN),
        predicate(_is_month, "is_month"),
    ),
    prod=_make_month_dom_interval,
)


# ---------------------------------------------------------------------------
# Public RULES tuple — the registry auto-discovers this name.

RULES: tuple[Rule, ...] = (
    _by_rule,
    # Year intervals
    _year_year_interval_rule,
    _from_year_to_year_rule,
    _between_year_and_year_rule,
    # <month> <dom1> .. <dom2>
    _month_dom_to_dom_rule,
    _from_month_dom_to_dom_rule,
    _month_dom_regex_to_dom_regex_rule,
    _from_month_dom_regex_to_dom_regex_rule,
    # <dom1> .. <dom2> [of] <month>
    _dom_to_dom_month_rule,
    _dom_to_dom_of_month_rule,
    _dom_regex_to_dom_regex_month_rule,
    _dom_regex_to_dom_regex_of_month_rule,
    _from_dom_to_dom_month_rule,
    _from_dom_to_dom_of_month_rule,
    _from_dom_regex_to_dom_regex_month_rule,
    _from_dom_regex_to_dom_regex_of_month_rule,
    _the_dom_to_the_dom_of_month_rule,
    _the_dom_regex_to_the_dom_regex_of_month_rule,
)
