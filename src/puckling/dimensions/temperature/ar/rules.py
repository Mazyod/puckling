"""Temperature rules — Arabic.

Ported from Duckling/Temperature/AR/Rules.hs.
"""

from __future__ import annotations

from puckling.dimensions.numeral.helpers import parse_arabic_decimal
from puckling.dimensions.numeral.types import NumeralValue
from puckling.dimensions.temperature.types import TemperatureUnit, TemperatureValue
from puckling.predicates import is_numeral
from puckling.types import Rule, Token, predicate, regex


def _is_temperature_with_value(t: Token) -> bool:
    if t.dim != "temperature":
        return False
    return getattr(t.value, "value", None) is not None


def _value_of(t: Token) -> float | int | None:
    """Extract the numeric value from a numeral or temperature token."""
    v = getattr(t.value, "value", None)
    return v if isinstance(v, (int, float)) else None


def _temp(value: float | int, unit: TemperatureUnit | None) -> Token:
    return Token(dim="temperature", value=TemperatureValue(value=value, unit=unit))


def _with_unit(unit: TemperatureUnit):
    """Build a production that lifts the head token's value into a temperature with `unit`."""

    def prod(tokens: tuple[Token, ...]) -> Token | None:
        n = _value_of(tokens[0])
        return None if n is None else _temp(n, unit)

    return prod


# Seed: parse a bare numeric literal (Arabic-Indic ٠-٩ or ASCII digits, with
# optional decimal and leading minus). The foundation may also produce numerals
# from spelled-out forms; this rule only ensures any digit string surfaces.
def _prod_integer_numeral(tokens: tuple[Token, ...]) -> Token | None:
    text = tokens[0].value.text
    try:
        value: int | float = parse_arabic_decimal(text)
    except ValueError:
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return Token(dim="numeral", value=NumeralValue(value=value))


_integer_numeral_rule = Rule(
    name="integer (numeric, AR)",
    pattern=(regex(r"-?[٠-٩]+(?:[.٫][٠-٩]+)?|-?\d+(?:\.\d+)?"),),
    prod=_prod_integer_numeral,
)


# <numeral> درجة / ° → degree temperature (no specific unit).
_rule_temperature_degrees = Rule(
    name="<latent temp> degrees",
    pattern=(
        predicate(is_numeral, "is_numeral"),
        regex(r"(?:درج(?:[ةه]|ات)(?:\s*مئوي[ةه])?)|°"),
    ),
    prod=_with_unit(TemperatureUnit.DEGREE),
)


# درجتين / درجتان → 2 degrees.
_rule_temperature_two_degrees = Rule(
    name="two degrees",
    pattern=(regex(r"درجت(?:ين|ان)"),),
    prod=lambda _t: _temp(2, TemperatureUnit.DEGREE),
)


# <temp> سلزيوس — promotes a degree-temperature into CELSIUS (e.g. "37° سلزيوس").
_rule_temperature_celsius = Rule(
    name="<temp> Celsius",
    pattern=(
        predicate(_is_temperature_with_value, "is_temperature"),
        regex(r"(?:درج(?:[ةه]|ات)\s+)?سي?لي?[سز]ي?وس"),
    ),
    prod=_with_unit(TemperatureUnit.CELSIUS),
)


# <numeral> سلزيوس — also accept "<n> سلزيوس" / "<n> درجة سلزيوس" directly.
_rule_numeral_celsius = Rule(
    name="<numeral> Celsius",
    pattern=(
        predicate(is_numeral, "is_numeral"),
        regex(r"(?:درج(?:[ةه]|ات)\s+)?سي?لي?[سز]ي?وس"),
    ),
    prod=_with_unit(TemperatureUnit.CELSIUS),
)


# "<n> درجة مئوية" — explicit Celsius spelling. Note: upstream treats this as
# DEGREE in the "درجه" variant, but the task spec asks for CELSIUS on the "ة"
# variant. We restrict to that variant; "درجه مئوية" continues to fall through
# to the generic DEGREE rule.
_rule_numeral_celsius_explicit = Rule(
    name="<numeral> درجة مئوية",
    pattern=(
        predicate(is_numeral, "is_numeral"),
        regex(r"درجة\s+مئوية|°?\s*س"),
    ),
    prod=_with_unit(TemperatureUnit.CELSIUS),
)


# <temp> فهرنهايت — promotes a degree-temperature into FAHRENHEIT.
_rule_temperature_fahrenheit = Rule(
    name="<temp> Fahrenheit",
    pattern=(
        predicate(_is_temperature_with_value, "is_temperature"),
        regex(r"(?:درج(?:[ةه]|ات)\s+)?ف(?:ا|ي)?هرنها?يت"),
    ),
    prod=_with_unit(TemperatureUnit.FAHRENHEIT),
)


_rule_numeral_fahrenheit = Rule(
    name="<numeral> Fahrenheit",
    pattern=(
        predicate(is_numeral, "is_numeral"),
        regex(r"(?:درج(?:[ةه]|ات)\s+)?ف(?:ا|ي)?هرنها?يت"),
    ),
    prod=_with_unit(TemperatureUnit.FAHRENHEIT),
)


# <temp> below zero — negate. If no unit was set, default to DEGREE.
def _prod_below_zero(tokens: tuple[Token, ...]) -> Token | None:
    td = tokens[0].value
    if td.value is None:
        return None
    return _temp(-td.value, td.unit if td.unit is not None else TemperatureUnit.DEGREE)


_rule_below_zero_temp = Rule(
    name="<temp> below zero",
    pattern=(
        predicate(_is_temperature_with_value, "is_temperature"),
        regex(r"تحت\s+الصفر"),
    ),
    prod=_prod_below_zero,
)


# <numeral> below zero — handles "2 تحت الصفر" without an intervening "درجة".
def _prod_below_zero_numeral(tokens: tuple[Token, ...]) -> Token | None:
    n = _value_of(tokens[0])
    return None if n is None else _temp(-n, TemperatureUnit.DEGREE)


_rule_below_zero_numeral = Rule(
    name="<numeral> below zero",
    pattern=(
        predicate(is_numeral, "is_numeral"),
        regex(r"تحت\s+الصفر"),
    ),
    prod=_prod_below_zero_numeral,
)


# Leading "-" before a temperature → negate. Handles "- 2 درجة" where the minus
# is detached from the digit and the seed numeral rule cannot capture it.
def _prod_negate_temp(tokens: tuple[Token, ...]) -> Token | None:
    td = tokens[1].value
    if td.value is None:
        return None
    return _temp(-td.value, td.unit)


_rule_negate_temp = Rule(
    name="- <temp>",
    pattern=(
        regex(r"-"),
        predicate(_is_temperature_with_value, "is_temperature"),
    ),
    prod=_prod_negate_temp,
)


# Order matters for ties in winner selection: rules listed earlier produce
# tokens earlier and win when two candidates cover identical spans. Specific
# (Celsius/Fahrenheit) rules precede the generic Degree rule.
RULES: tuple[Rule, ...] = (
    _integer_numeral_rule,
    _rule_numeral_celsius_explicit,
    _rule_numeral_celsius,
    _rule_numeral_fahrenheit,
    _rule_temperature_celsius,
    _rule_temperature_fahrenheit,
    _rule_temperature_degrees,
    _rule_temperature_two_degrees,
    _rule_below_zero_temp,
    _rule_below_zero_numeral,
    _rule_negate_temp,
)
