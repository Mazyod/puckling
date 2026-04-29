"""Volume rules for Arabic.

Ported from Duckling's ``Duckling/Volume/AR/Rules.hs``. Covers the main metric
units (millilitre, litre, hectolitre) plus gallon, with several handcrafted
phrases for fractional and dual-form litre measurements.
"""

from __future__ import annotations

from puckling.dimensions.numeral.helpers import parse_arabic_decimal
from puckling.dimensions.numeral.types import NumeralValue
from puckling.dimensions.volume.types import VolumeUnit, VolumeValue
from puckling.predicates import is_numeral
from puckling.types import Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# numeric handling — emit a numeral from Arabic-Indic or ASCII digits.

_NUMERIC_BOUND_L = r"(?<![\p{L}\p{N}.,٫٬،+\-/])"
_TOKEN_BOUND_R = r"(?![\p{L}\p{N}_]|[-/])"
_NUMBER_PATTERN = rf"{_NUMERIC_BOUND_L}(?:[٠-٩]+(?:٫[٠-٩]+)?|\d+(?:\.\d+)?)"


def _bounded(pattern: str) -> str:
    return rf"(?:{pattern}){_TOKEN_BOUND_R}"


def _prod_number(tokens: tuple[Token, ...]) -> Token | None:
    value = parse_arabic_decimal(tokens[0].value.text)
    return Token(dim="numeral", value=NumeralValue(value=value))


_rule_number = Rule(
    name="integer/decimal (numeric)",
    pattern=(regex(_NUMBER_PATTERN),),
    prod=_prod_number,
)


# ---------------------------------------------------------------------------
# <n> <unit> rules.


def _make_number_unit_rule(name: str, unit_pattern: str, unit: VolumeUnit) -> Rule:
    """Build a ``<n> <unit>`` rule: numeral followed by the unit regex."""

    def prod(tokens: tuple[Token, ...]) -> Token | None:
        n = tokens[0].value.value
        return Token(dim="volume", value=VolumeValue(value=n, unit=unit))

    return Rule(
        name=name,
        pattern=(predicate(is_numeral, "is_numeral"), regex(_bounded(unit_pattern))),
        prod=prod,
    )


_rule_n_millilitre = _make_number_unit_rule(
    name="<n> ml",
    unit_pattern=r"مي?لي?( ?لي?تي?ر)?",
    unit=VolumeUnit.MILLILITRE,
)

_rule_n_hectolitre = _make_number_unit_rule(
    name="<n> hectoliters",
    unit_pattern=r"هي?كتو ?لي?تر",
    unit=VolumeUnit.HECTOLITRE,
)

_rule_n_litre = _make_number_unit_rule(
    name="<n> liters",
    unit_pattern=r"لي?تي?ر(ات)?",
    unit=VolumeUnit.LITRE,
)

_rule_n_gallon = _make_number_unit_rule(
    name="<n> gallon",
    unit_pattern=r"[جغق]الون(ين|ان|ات)?",
    unit=VolumeUnit.GALLON,
)


# ---------------------------------------------------------------------------
# Standalone phrases — a single regex carrying both value and unit.


def _make_litre_phrase_rule(name: str, pattern: str, value: float) -> Rule:
    def prod(_tokens: tuple[Token, ...]) -> Token | None:
        return Token(dim="volume", value=VolumeValue(value=value, unit=VolumeUnit.LITRE))

    return Rule(name=name, pattern=(regex(_bounded(pattern)),), prod=prod)


_rule_quarter_litre = _make_litre_phrase_rule(
    name="quarter liter",
    pattern=r"ربع لي?تي?ر",
    value=0.25,
)

_rule_half_litre = _make_litre_phrase_rule(
    name="half liter",
    pattern=r"نصف? لي?تي?ر",
    value=0.5,
)

_rule_two_litres = _make_litre_phrase_rule(
    name="two liters",
    pattern=r"لي?تي?ر(ان|ين)",
    value=2,
)

_rule_litre_and_half = _make_litre_phrase_rule(
    name="liter and half",
    pattern=r"لي?تي?ر و ?نصف?",
    value=1.5,
)

_rule_litre_and_quarter = _make_litre_phrase_rule(
    name="liter and quarter",
    pattern=r"لي?تي?ر و ?ربع",
    value=1.25,
)


RULES: tuple[Rule, ...] = (
    _rule_number,
    _rule_half_litre,
    _rule_quarter_litre,
    _rule_two_litres,
    _rule_litre_and_half,
    _rule_litre_and_quarter,
    _rule_n_millilitre,
    _rule_n_hectolitre,
    _rule_n_litre,
    _rule_n_gallon,
)
