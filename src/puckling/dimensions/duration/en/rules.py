"""English Duration rules — port of `Duckling/Duration/EN/Rules.hs`.

Also contains:

* A port of `Duckling/TimeGrain/EN/Rules.hs` (grain words → `time_grain` tokens),
  since Duration cannot compose without grain tokens and the foundation does not
  yet ship a separate TimeGrain dimension.
* A small digit/word numeral fallback so the corpus can be exercised before the
  full Numeral EN port lands. These are marked
  ``# TODO(puckling): edge case`` and should be retired once Numeral EN is
  available — they exist purely so this unit's tests can run in isolation.
"""

from __future__ import annotations

from puckling.dimensions.duration.types import (
    _SECONDS_PER_GRAIN,
    DurationValue,
    duration,
)
from puckling.dimensions.numeral.types import NumeralValue
from puckling.dimensions.time.grain import Grain
from puckling.predicates import is_duration, is_grain, is_natural, number_between
from puckling.types import Predicate, RegexMatch, Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Numeral fallback (digit + a few common English number words).
#
# TODO(puckling): edge case — remove once Duckling/Numeral/EN ships in puckling.

_WORD_INTEGERS: dict[str, int] = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
}


def _prod_integer(tokens: tuple[Token, ...]) -> Token | None:
    text = tokens[0].value.text
    try:
        n: int | float = int(text)
    except ValueError:
        return None
    return Token(dim="numeral", value=NumeralValue(value=n))


def _prod_decimal(tokens: tuple[Token, ...]) -> Token | None:
    text = tokens[0].value.text
    try:
        n = float(text)
    except ValueError:
        return None
    return Token(dim="numeral", value=NumeralValue(value=n))


def _prod_integer_word(tokens: tuple[Token, ...]) -> Token | None:
    text = tokens[0].value.text.lower()
    n = _WORD_INTEGERS.get(text)
    if n is None:
        return None
    return Token(dim="numeral", value=NumeralValue(value=n))


_rule_integer_digits = Rule(
    name="integer (digits) [duration fallback]",
    pattern=(regex(r"\d+"),),
    prod=_prod_integer,
)

_rule_decimal_digits = Rule(
    name="decimal (digits) [duration fallback]",
    pattern=(regex(r"\d+\.\d+"),),
    prod=_prod_decimal,
)

_rule_integer_words = Rule(
    name="integer (word) [duration fallback]",
    pattern=(
        regex(
            r"(zero|one|two|three|four|five|six|seven|eight|nine|ten"
            r"|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen"
            r"|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy"
            r"|eighty|ninety|hundred)"
        ),
    ),
    prod=_prod_integer_word,
)


# ---------------------------------------------------------------------------
# TimeGrain EN — grain word → time_grain token.

_GRAINS: tuple[tuple[str, str, Grain], ...] = (
    ("second (grain)", r"sec(ond)?s?", Grain.SECOND),
    ("minute (grain)", r"m(in(ute)?s?)?", Grain.MINUTE),
    ("hour (grain)", r"h(((ou)?rs?)|r)?", Grain.HOUR),
    ("day (grain)", r"days?", Grain.DAY),
    ("week (grain)", r"weeks?", Grain.WEEK),
    ("month (grain)", r"months?", Grain.MONTH),
    ("quarter (grain)", r"(quarter|qtr)s?", Grain.QUARTER),
    ("year (grain)", r"y(ea)?rs?", Grain.YEAR),
)


def _grain_rule(name: str, pattern: str, grain: Grain) -> Rule:
    def prod(_tokens: tuple[Token, ...]) -> Token | None:
        return Token(dim="time_grain", value=grain)

    return Rule(name=name, pattern=(regex(pattern),), prod=prod)


_grain_rules: tuple[Rule, ...] = tuple(
    _grain_rule(name, pat, g) for (name, pat, g) in _GRAINS
)


# ---------------------------------------------------------------------------
# Duration helpers (mirrors `Duckling/Duration/Helpers.hs`).


def _n_plus_one_half(grain: Grain, n: int) -> DurationValue | None:
    """Return ``n + 0.5`` of ``grain`` expressed in the next finer grain."""
    if grain is Grain.MINUTE:
        return duration(30 + 60 * n, Grain.SECOND)
    if grain is Grain.HOUR:
        return duration(30 + 60 * n, Grain.MINUTE)
    if grain is Grain.DAY:
        return duration(12 + 24 * n, Grain.HOUR)
    if grain is Grain.MONTH:
        return duration(15 + 30 * n, Grain.DAY)
    if grain is Grain.YEAR:
        return duration(6 + 12 * n, Grain.MONTH)
    return None


def _minutes_from_hour_mixed_fraction(h: int, num: int, den: int) -> DurationValue:
    """``H.NUM/DEN`` hours → minutes (Duckling's helper)."""
    return duration(60 * h + (num * 60) // den, Grain.MINUTE)


def _seconds_from_hour_mixed_fraction(m: int, s: int, den: int) -> DurationValue:
    return duration(60 * m + (s * 60) // den, Grain.SECOND)


def _to_seconds(d: DurationValue) -> int:
    return d.value * _SECONDS_PER_GRAIN[d.grain]


def _combine(
    coarse: DurationValue, fine: DurationValue
) -> DurationValue | None:
    """Sum two durations, expressed in the *finer* grain.

    Mirrors Duckling's ``Semigroup DurationData`` instance, which converts both
    sides through their seconds equivalent and then re-expresses the sum in the
    finer grain. Returns ``None`` if ``coarse`` is not strictly coarser than
    ``fine`` (the upstream rule's ``g > dg`` guard).
    """
    if not coarse.grain.is_coarser_than(fine.grain):
        return None
    seconds = _to_seconds(coarse) + _to_seconds(fine)
    per = _SECONDS_PER_GRAIN[fine.grain]
    return duration(seconds // per, fine.grain)


def _is_grain_of(target: Grain) -> Predicate:
    """Predicate: token is a `time_grain` carrying exactly ``target``."""

    def go(t: Token) -> bool:
        return is_grain(t) and t.value is target

    return go


def _natural_int(t: Token) -> int | None:
    v = getattr(t.value, "value", None)
    if isinstance(v, int) and v >= 0:
        return v
    if isinstance(v, float) and v.is_integer() and v >= 0:
        return int(v)
    return None


# ---------------------------------------------------------------------------
# Duration rules.


def _prod_integer_grain(tokens: tuple[Token, ...]) -> Token | None:
    n = _natural_int(tokens[0])
    if n is None:
        return None
    grain: Grain = tokens[1].value
    return Token(dim="duration", value=duration(n, grain))


# Mirrors `Duckling/Duration/Rules.hs` (locale-agnostic), included here because
# the foundation does not yet expose a shared duration rule module.
_rule_integer_grain = Rule(
    name="<integer> <unit-of-duration>",
    pattern=(
        predicate(is_natural, "is_natural"),
        predicate(is_grain, "is_grain"),
    ),
    prod=_prod_integer_grain,
)


def _prod_quarter_of_an_hour(_tokens: tuple[Token, ...]) -> Token | None:
    return Token(dim="duration", value=duration(15, Grain.MINUTE))


_rule_quarter_of_an_hour = Rule(
    name="quarter of an hour",
    pattern=(regex(r"(1/4\s?h(our)?|(a\s)?quarter of an hour)"),),
    prod=_prod_quarter_of_an_hour,
)


def _prod_half_hour_abbrev(_tokens: tuple[Token, ...]) -> Token | None:
    return Token(dim="duration", value=duration(30, Grain.MINUTE))


_rule_half_hour_abbrev = Rule(
    name="half an hour (abbrev).",
    pattern=(regex(r"1/2\s?h"),),
    prod=_prod_half_hour_abbrev,
)


def _prod_three_quarters_of_an_hour(_tokens: tuple[Token, ...]) -> Token | None:
    return Token(dim="duration", value=duration(45, Grain.MINUTE))


_rule_three_quarters_of_an_hour = Rule(
    name="three-quarters of an hour",
    pattern=(regex(r"(3/4\s?h(our)?|three(\s|-)quarters of an hour)"),),
    prod=_prod_three_quarters_of_an_hour,
)


def _prod_fortnight(_tokens: tuple[Token, ...]) -> Token | None:
    return Token(dim="duration", value=duration(14, Grain.DAY))


_rule_fortnight = Rule(
    name="fortnight",
    pattern=(regex(r"(a|one)?\s?fortnight"),),
    prod=_prod_fortnight,
)


def _prod_numeral_quotes(tokens: tuple[Token, ...]) -> Token | None:
    n = _natural_int(tokens[0])
    if n is None:
        return None
    rm = tokens[1].value
    assert isinstance(rm, RegexMatch)
    mark = rm.groups[0] if rm.groups else rm.text
    if mark == "'":
        return Token(dim="duration", value=duration(n, Grain.MINUTE))
    if mark == '"':
        return Token(dim="duration", value=duration(n, Grain.SECOND))
    return None


_rule_numeral_quotes = Rule(
    name="<integer> + '\"",
    pattern=(
        predicate(is_natural, "is_natural"),
        regex(r"(['\"])"),
    ),
    prod=_prod_numeral_quotes,
)


def _prod_numeral_more(tokens: tuple[Token, ...]) -> Token | None:
    n = _natural_int(tokens[0])
    if n is None:
        return None
    grain: Grain = tokens[2].value
    return Token(dim="duration", value=duration(n, grain))


_rule_numeral_more = Rule(
    name="<integer> more <unit-of-duration>",
    pattern=(
        predicate(is_natural, "is_natural"),
        regex(r"more|additional|extra|less|fewer"),
        predicate(is_grain, "is_grain"),
    ),
    prod=_prod_numeral_more,
)


def _prod_dot_number_hours(tokens: tuple[Token, ...]) -> Token | None:
    rm = tokens[0].value
    assert isinstance(rm, RegexMatch)
    h_str, m_str = rm.groups[0], rm.groups[1]
    if h_str is None or m_str is None:
        return None
    h = int(h_str)
    num = int(m_str)
    den = 10 ** len(m_str)
    return Token(
        dim="duration",
        value=_minutes_from_hour_mixed_fraction(h, num, den),
    )


_rule_dot_number_hours = Rule(
    name="number.number hours",
    pattern=(
        regex(r"(\d+)\.(\d+)"),
        predicate(_is_grain_of(Grain.HOUR), "is_grain hour"),
    ),
    prod=_prod_dot_number_hours,
)


def _prod_and_half_hour(tokens: tuple[Token, ...]) -> Token | None:
    n = _natural_int(tokens[0])
    if n is None:
        return None
    return Token(dim="duration", value=duration(30 + 60 * n, Grain.MINUTE))


_rule_and_half_hour = Rule(
    name="<integer> and an half hour",
    pattern=(
        predicate(is_natural, "is_natural"),
        regex(r"and (an? )?half hours?"),
    ),
    prod=_prod_and_half_hour,
)


def _prod_and_half_minute(tokens: tuple[Token, ...]) -> Token | None:
    n = _natural_int(tokens[0])
    if n is None:
        return None
    return Token(dim="duration", value=duration(30 + 60 * n, Grain.SECOND))


_rule_and_half_minute = Rule(
    name="<integer> and a half minutes",
    pattern=(
        predicate(is_natural, "is_natural"),
        regex(r"and (an? )?half min(ute)?s?"),
    ),
    prod=_prod_and_half_minute,
)


def _prod_a_grain(tokens: tuple[Token, ...]) -> Token | None:
    grain: Grain = tokens[1].value
    return Token(dim="duration", value=duration(1, grain))


_rule_a_grain = Rule(
    name="a <unit-of-duration>",
    pattern=(
        regex(r"an?"),
        predicate(is_grain, "is_grain"),
    ),
    prod=_prod_a_grain,
)


def _prod_half_a_grain(tokens: tuple[Token, ...]) -> Token | None:
    grain: Grain = tokens[1].value
    dv = _n_plus_one_half(grain, 0)
    if dv is None:
        return None
    return Token(dim="duration", value=dv)


_rule_half_a_grain = Rule(
    name="half a <time-grain>",
    pattern=(
        regex(r"(1/2|half)( an?)?"),
        predicate(is_grain, "is_grain"),
    ),
    prod=_prod_half_a_grain,
)


def _prod_one_grain_and_half(tokens: tuple[Token, ...]) -> Token | None:
    grain: Grain = tokens[1].value
    dv = _n_plus_one_half(grain, 1)
    if dv is None:
        return None
    return Token(dim="duration", value=dv)


_rule_one_grain_and_half = Rule(
    name="a <unit-of-duration> and a half",
    pattern=(
        regex(r"an?|one"),
        predicate(is_grain, "is_grain"),
        regex(r"and (a )?half"),
    ),
    prod=_prod_one_grain_and_half,
)


def _prod_hours_and_minutes(tokens: tuple[Token, ...]) -> Token | None:
    h = _natural_int(tokens[0])
    m = _natural_int(tokens[2])
    if h is None or m is None:
        return None
    return Token(dim="duration", value=duration(60 * h + m, Grain.MINUTE))


_is_natural_under_60 = number_between(1, 60)


def _natural_minute(t: Token) -> bool:
    return is_natural(t) and _is_natural_under_60(t)


_rule_hours_and_minutes = Rule(
    name="<integer> hour and <integer>",
    pattern=(
        predicate(is_natural, "is_natural"),
        regex(r"hours?( and)?"),
        predicate(_natural_minute, "is_natural & 1..60"),
    ),
    prod=_prod_hours_and_minutes,
)


def _prod_precision(tokens: tuple[Token, ...]) -> Token | None:
    return tokens[1]


_rule_precision = Rule(
    name="about|exactly <duration>",
    pattern=(
        regex(r"(about|around|approximately|exactly)"),
        predicate(is_duration, "is_duration"),
    ),
    prod=_prod_precision,
)


def _prod_composite_commas_and(tokens: tuple[Token, ...]) -> Token | None:
    n = _natural_int(tokens[0])
    if n is None:
        return None
    g: Grain = tokens[1].value
    inner: DurationValue = tokens[3].value
    combined = _combine(duration(n, g), inner)
    if combined is None:
        return None
    return Token(dim="duration", value=combined)


_rule_composite_commas_and = Rule(
    name="composite <duration> (with ,/and)",
    pattern=(
        predicate(is_natural, "is_natural"),
        predicate(is_grain, "is_grain"),
        regex(r",|and"),
        predicate(is_duration, "is_duration"),
    ),
    prod=_prod_composite_commas_and,
)


def _prod_composite(tokens: tuple[Token, ...]) -> Token | None:
    n = _natural_int(tokens[0])
    if n is None:
        return None
    g: Grain = tokens[1].value
    inner: DurationValue = tokens[2].value
    combined = _combine(duration(n, g), inner)
    if combined is None:
        return None
    return Token(dim="duration", value=combined)


_rule_composite = Rule(
    name="composite <duration>",
    pattern=(
        predicate(is_natural, "is_natural"),
        predicate(is_grain, "is_grain"),
        predicate(is_duration, "is_duration"),
    ),
    prod=_prod_composite,
)


def _prod_composite_and(tokens: tuple[Token, ...]) -> Token | None:
    left: DurationValue = tokens[0].value
    right: DurationValue = tokens[2].value
    combined = _combine(left, right)
    if combined is None:
        return None
    return Token(dim="duration", value=combined)


_rule_composite_and = Rule(
    name="composite <duration> and <duration>",
    pattern=(
        predicate(is_duration, "is_duration"),
        regex(r",|and"),
        predicate(is_duration, "is_duration"),
    ),
    prod=_prod_composite_and,
)


def _prod_dot_number_minutes(tokens: tuple[Token, ...]) -> Token | None:
    rm = tokens[0].value
    assert isinstance(rm, RegexMatch)
    m_str, s_str = rm.groups[0], rm.groups[1]
    if m_str is None or s_str is None:
        return None
    m = int(m_str)
    s = int(s_str)
    den = 10 ** len(s_str)
    return Token(
        dim="duration",
        value=_seconds_from_hour_mixed_fraction(m, s, den),
    )


_rule_dot_number_minutes = Rule(
    name="number.number minutes",
    pattern=(
        regex(r"(\d+)\.(\d+)"),
        predicate(_is_grain_of(Grain.MINUTE), "is_grain minute"),
    ),
    prod=_prod_dot_number_minutes,
)


def _prod_n_and_quarter_hour(tokens: tuple[Token, ...]) -> Token | None:
    h = _natural_int(tokens[0])
    if h is None:
        return None
    rm = tokens[1].value
    assert isinstance(rm, RegexMatch)
    mark = (rm.groups[0] or "").strip().lower() if rm.groups else ""
    q = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3}.get(mark, 1)
    return Token(dim="duration", value=duration(15 * q + 60 * h, Grain.MINUTE))


_rule_n_and_quarter_hour = Rule(
    name="<Integer> and <Integer> quarter of hour",
    pattern=(
        predicate(is_natural, "is_natural"),
        regex(r"and (a |an |one |two |three )?quarters?( of)?( an)?"),
        predicate(_is_grain_of(Grain.HOUR), "is_grain hour"),
    ),
    prod=_prod_n_and_quarter_hour,
)


# ---------------------------------------------------------------------------

RULES: tuple[Rule, ...] = (
    # numeral fallbacks (TODO: edge case — drop once Numeral EN ships)
    _rule_decimal_digits,
    _rule_integer_digits,
    _rule_integer_words,
    # time grain
    *_grain_rules,
    # duration
    _rule_integer_grain,
    _rule_composite_commas_and,
    _rule_quarter_of_an_hour,
    _rule_half_hour_abbrev,
    _rule_three_quarters_of_an_hour,
    _rule_fortnight,
    _rule_numeral_more,
    _rule_dot_number_hours,
    _rule_and_half_hour,
    _rule_and_half_minute,
    _rule_a_grain,
    _rule_half_a_grain,
    _rule_one_grain_and_half,
    _rule_hours_and_minutes,
    _rule_precision,
    _rule_numeral_quotes,
    _rule_composite,
    _rule_composite_and,
    _rule_dot_number_minutes,
    _rule_n_and_quarter_hour,
)
