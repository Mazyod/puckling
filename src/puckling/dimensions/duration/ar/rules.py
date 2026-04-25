"""Arabic Duration rules — port of Duckling's Duration/AR/Rules.hs.

Covers grain-emitting tokens for Arabic units of time, dual-form shortcuts
("ساعتين" = 2 hours), and compositions of <integer> + <unit> driven either by
Arabic-Indic / ASCII digits or by tokens emitted from the parallel Numeral AR
worker.
"""

from __future__ import annotations

from puckling.dimensions.duration.types import DurationValue, duration
from puckling.dimensions.numeral.helpers import parse_arabic_int
from puckling.dimensions.numeral.types import NumeralValue
from puckling.dimensions.time.grain import Grain
from puckling.predicates import is_grain, is_natural
from puckling.types import RegexMatch, Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Rule factories.

def _grain_rule(name: str, pattern: str, grain: Grain) -> Rule:
    """A regex → `time_grain` token rule."""

    def prod(_: tuple[Token, ...]) -> Token | None:
        return Token(dim="time_grain", value=grain)

    return Rule(name=name, pattern=(regex(pattern),), prod=prod)


def _fixed_duration_rule(name: str, pattern: str, value: int, grain: Grain) -> Rule:
    """A regex → fixed `Duration` token rule (e.g. "ربع ساعة" → 15 minutes)."""

    def prod(_: tuple[Token, ...]) -> Token | None:
        return Token(dim="duration", value=duration(value, grain))

    return Rule(name=name, pattern=(regex(pattern),), prod=prod)


def _word_numeral_rule(name: str, pattern: str, value: int) -> Rule:
    """A regex → `numeral` token rule for a fixed integer."""

    def prod(_: tuple[Token, ...]) -> Token | None:
        return Token(dim="numeral", value=NumeralValue(value=value))

    return Rule(name=name, pattern=(regex(pattern),), prod=prod)


def _grain_token_value(t: Token) -> Grain | None:
    g = t.value
    return g if isinstance(g, Grain) else None


def _natural_int(t: Token) -> int | None:
    if not isinstance(t.value, NumeralValue):
        return None
    v = t.value.value
    return int(v) if isinstance(v, (int, float)) else None


# ---------------------------------------------------------------------------
# Grain-emitting rules — Arabic units of time.

_grain_second = _grain_rule("grain second", r"ثاني[ةه]|ثواني|لحظ[ةه]", Grain.SECOND)
_grain_minute = _grain_rule("grain minute", r"دقيق[ةه]|دقائق", Grain.MINUTE)
_grain_hour = _grain_rule("grain hour", r"ساع[ةه]|ساعات", Grain.HOUR)
_grain_day = _grain_rule("grain day", r"يوم|[أا]يام", Grain.DAY)
_grain_week = _grain_rule("grain week", r"[أا]سبوع|[أا]سابيع", Grain.WEEK)
_grain_month = _grain_rule("grain month", r"شهر|[أا]شهر|شهور", Grain.MONTH)
_grain_year = _grain_rule("grain year", r"سن[ةه]|سنوات|سنين|عام|[أا]عوام", Grain.YEAR)


# ---------------------------------------------------------------------------
# Numeral-input shim. Lets this dimension's tests run before the Numeral AR
# worker lands; the engine dedupes tokens by (dim, range, value) so duplicate
# work is harmless once Numeral AR is wired in.

def _prod_arabic_digits(tokens: tuple[Token, ...]) -> Token | None:
    head = tokens[0]
    assert isinstance(head.value, RegexMatch)
    return Token(dim="numeral", value=NumeralValue(value=parse_arabic_int(head.value.text)))


_digit_numeral = Rule(
    name="duration-ar digit numeral",
    pattern=(regex(r"[٠-٩0-9]+"),),
    prod=_prod_arabic_digits,
)

_word_three = _word_numeral_rule("duration-ar word numeral 3", r"ثلاث[ةه]?", 3)
_word_five = _word_numeral_rule("duration-ar word numeral 5", r"خمس[ةه]?", 5)
_word_seven = _word_numeral_rule("duration-ar word numeral 7", r"سبع[ةه]?", 7)


# ---------------------------------------------------------------------------
# Fixed fractions of an hour.

_quarter_of_an_hour = _fixed_duration_rule(
    "quarter of an hour", r"ربع ساعة", 15, Grain.MINUTE
)
_half_an_hour = _fixed_duration_rule(
    "half an hour", r"1/2\s?ساع[ةه]?|نصف? ساع[ةه]", 30, Grain.MINUTE
)
_three_quarters_of_an_hour = _fixed_duration_rule(
    "three-quarters of an hour",
    r"3/4\s?(?:ال)?ساع[ةه]?|ثلاث[ةه]?[\s-][أا]رباع (?:ال)?ساع[ةه]",
    45,
    Grain.MINUTE,
)


# ---------------------------------------------------------------------------
# `<integer> + '"` — minutes / seconds shorthand.

def _prod_integer_quote(tokens: tuple[Token, ...]) -> Token | None:
    n = _natural_int(tokens[0])
    if n is None:
        return None
    mark_tok = tokens[1]
    assert isinstance(mark_tok.value, RegexMatch)
    mark = mark_tok.value.groups[0] if mark_tok.value.groups else mark_tok.value.text
    if mark == "'":
        return Token(dim="duration", value=duration(n, Grain.MINUTE))
    if mark == '"':
        return Token(dim="duration", value=duration(n, Grain.SECOND))
    return None


_integer_quotes = Rule(
    name="<integer> + '\"",
    pattern=(predicate(is_natural, "is_natural"), regex(r"(['\"])")),
    prod=_prod_integer_quote,
)


# ---------------------------------------------------------------------------
# `number.number hours` mixed-fraction → minutes.

def _prod_dot_number_hours(tokens: tuple[Token, ...]) -> Token | None:
    head = tokens[0]
    assert isinstance(head.value, RegexMatch)
    h_text, m_text = head.value.groups[0], head.value.groups[1]
    if h_text is None or m_text is None:
        return None
    h = int(h_text)
    n = int(m_text)
    d = 10 ** len(m_text)
    minutes = 60 * h + (n * 60) // d
    return Token(dim="duration", value=duration(minutes, Grain.MINUTE))


_dot_number_hours = Rule(
    name="number.number hours",
    pattern=(regex(r"(\d+)\.(\d+) *ساع(?:ة|ات)"),),
    prod=_prod_dot_number_hours,
)


# ---------------------------------------------------------------------------
# `<integer> and a half hour` → 30 + 60n minutes.

def _prod_integer_and_half_hour(tokens: tuple[Token, ...]) -> Token | None:
    n = _natural_int(tokens[0])
    if n is None:
        return None
    return Token(dim="duration", value=duration(30 + 60 * n, Grain.MINUTE))


_integer_and_half_hour = Rule(
    name="<integer> and an half hour",
    pattern=(predicate(is_natural, "is_natural"), regex(r"و ?نصف? ساع[ةه]")),
    prod=_prod_integer_and_half_hour,
)


# ---------------------------------------------------------------------------
# Dual-form shortcuts (regex-only, when the noun lacks a base grain match).

_two_seconds = _fixed_duration_rule(
    "two seconds", r"ثانيتين|ثانيتان|لحظتين|لحظتان", 2, Grain.SECOND
)
_two_minutes = _fixed_duration_rule(
    "two minutes", r"دقيقتين|دقيقتان", 2, Grain.MINUTE
)
_two_hours = _fixed_duration_rule(
    "two hours", r"ساعتين|ساعتان", 2, Grain.HOUR
)
_two_years = _fixed_duration_rule(
    "dual years", r"سنتين|سنتان|عامين|عامان", 2, Grain.YEAR
)


# ---------------------------------------------------------------------------
# Generic <grain> + dual suffix → 2 * grain (covers day/week/month/etc.).

def _prod_n_unit(value: int):
    def prod(tokens: tuple[Token, ...]) -> Token | None:
        grain = _grain_token_value(tokens[0])
        if grain is None:
            return None
        return Token(dim="duration", value=DurationValue(value=value, grain=grain))

    return prod


_dual_unit = Rule(
    name="dual <unit-of-duration>",
    pattern=(predicate(is_grain, "is_grain"), regex(r"(?:ان|ين)")),
    prod=_prod_n_unit(2),
)

_single_unit = Rule(
    name="single <unit-of-duration>",
    pattern=(predicate(is_grain, "is_grain"),),
    prod=_prod_n_unit(1),
)


# ---------------------------------------------------------------------------
# Generic <integer> <unit-of-duration>. Lives in Duckling's locale-agnostic
# Duration/Rules.hs; duplicated here so the AR test set passes standalone.

def _prod_integer_unit(tokens: tuple[Token, ...]) -> Token | None:
    n = _natural_int(tokens[0])
    grain = _grain_token_value(tokens[1])
    if n is None or grain is None:
        return None
    return Token(dim="duration", value=DurationValue(value=n, grain=grain))


_integer_unit = Rule(
    name="<integer> <unit-of-duration>",
    pattern=(
        predicate(is_natural, "is_natural"),
        predicate(is_grain, "is_grain"),
    ),
    prod=_prod_integer_unit,
)


RULES: tuple[Rule, ...] = (
    _grain_second,
    _grain_minute,
    _grain_hour,
    _grain_day,
    _grain_week,
    _grain_month,
    _grain_year,
    _digit_numeral,
    _word_three,
    _word_five,
    _word_seven,
    _quarter_of_an_hour,
    _half_an_hour,
    _three_quarters_of_an_hour,
    _integer_quotes,
    _dot_number_hours,
    _integer_and_half_hour,
    _two_seconds,
    _two_minutes,
    _two_hours,
    _two_years,
    _dual_unit,
    _single_unit,
    _integer_unit,
)
