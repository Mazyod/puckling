"""English Temperature rules — port of Duckling/Temperature/EN/Rules.hs.

Mirrors:
  - https://github.com/facebook/duckling/blob/main/Duckling/Temperature/Rules.hs
    (the locale-agnostic Numeral->Temperature converter, included here so this
    EN unit is self-contained per the porting plan)
  - https://github.com/facebook/duckling/blob/main/Duckling/Temperature/EN/Rules.hs
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from puckling.dimensions.numeral.types import NumeralValue
from puckling.dimensions.temperature.types import (
    TemperatureIntervalDirection,
    TemperatureIntervalValue,
    TemperatureOpenIntervalValue,
    TemperatureUnit,
    TemperatureValue,
)
from puckling.predicates import is_numeral
from puckling.types import Predicate, Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Predicates


def _is_value_only(allow_degree: bool) -> Predicate:
    """Mirror Duckling's ``isValueOnly``.

    Matches a temperature token that carries a single value with no min/max
    bounds. By default the unit must be absent; with ``allow_degree`` set the
    generic ``Degree`` unit is also accepted (so "70 degrees" can become
    "70 degrees Fahrenheit").
    """

    def go(t: Token) -> bool:
        if t.dim != "temperature" or not isinstance(t.value, TemperatureValue):
            return False
        v = t.value
        if v.value is None:
            return False
        unit = v.unit
        if unit is None:
            return True
        return allow_degree and unit is TemperatureUnit.DEGREE

    return go


_IS_VALUE_ONLY_STRICT = _is_value_only(False)
_IS_VALUE_ONLY_OR_DEGREE = _is_value_only(True)


def _is_simple_temperature(t: Token) -> bool:
    """Match any temperature token carrying a single point value."""
    return (
        t.dim == "temperature"
        and isinstance(t.value, TemperatureValue)
        and t.value.value is not None
    )


def _units_compatible(u1: TemperatureUnit | None, u2: TemperatureUnit) -> bool:
    return u1 is None or u1 is u2


# ---------------------------------------------------------------------------
# Productions


def _prod_numeral_seed(tokens: tuple[Token, ...]) -> Token | None:
    """Seed ``numeral`` tokens from raw digits (``r"-?\\d+(\\.\\d+)?"``)."""
    text = tokens[0].value.text
    try:
        value: int | float = float(text) if "." in text else int(text)
    except ValueError:  # pragma: no cover - regex guarantees a valid literal
        return None
    return Token(dim="numeral", value=NumeralValue(value=value))


def _prod_numeral_as_temp(tokens: tuple[Token, ...]) -> Token | None:
    """Cross-dim: any numeral becomes a latent (unit-less) temperature.

    Numeric type is preserved (int stays int) so the resolved JSON shape
    matches Duckling, which never widens whole numbers to floats.
    """
    n = tokens[0].value.value
    if not isinstance(n, (int, float)):
        return None
    return Token(
        dim="temperature",
        value=TemperatureValue(value=n, unit=None, latent=True),
    )


def _make_unit_rewriter(unit: TemperatureUnit) -> Callable[[tuple[Token, ...]], Token | None]:
    """Build a production that stamps ``unit`` onto a temperature token."""

    def go(tokens: tuple[Token, ...]) -> Token | None:
        td = tokens[0].value
        if not isinstance(td, TemperatureValue):
            return None
        return Token(dim="temperature", value=replace(td, unit=unit, latent=False))

    return go


def _prod_below_zero(tokens: tuple[Token, ...]) -> Token | None:
    td = tokens[0].value
    if not isinstance(td, TemperatureValue) or td.value is None:
        return None
    negated = -td.value
    unit = td.unit if td.unit is not None else TemperatureUnit.DEGREE
    return Token(
        dim="temperature",
        value=replace(td, value=negated, unit=unit, latent=False),
    )


def _make_interval_prod(
    lo_idx: int, hi_idx: int
) -> Callable[[tuple[Token, ...]], Token | None]:
    """Build a closed-interval production reading low/high temps at given indices."""

    def go(tokens: tuple[Token, ...]) -> Token | None:
        lo, hi = tokens[lo_idx].value, tokens[hi_idx].value
        if not (isinstance(lo, TemperatureValue) and isinstance(hi, TemperatureValue)):
            return None
        if lo.value is None or hi.value is None or hi.unit is None:
            return None
        if lo.value >= hi.value or not _units_compatible(lo.unit, hi.unit):
            return None
        return Token(
            dim="temperature",
            value=TemperatureIntervalValue(
                start=TemperatureValue(value=lo.value, unit=hi.unit),
                end=TemperatureValue(value=hi.value, unit=hi.unit),
            ),
        )

    return go


def _make_open_interval_prod(
    direction: TemperatureIntervalDirection,
) -> Callable[[tuple[Token, ...]], Token | None]:
    """Build an open-interval production (>= bound or <= bound)."""

    def go(tokens: tuple[Token, ...]) -> Token | None:
        td = tokens[1].value
        if not isinstance(td, TemperatureValue) or td.value is None or td.unit is None:
            return None
        return Token(
            dim="temperature",
            value=TemperatureOpenIntervalValue(
                bound=TemperatureValue(value=td.value, unit=td.unit),
                direction=direction,
            ),
        )

    return go


# ---------------------------------------------------------------------------
# Rules

_VALUE_ONLY = predicate(_IS_VALUE_ONLY_STRICT, "is_value_only")
_VALUE_ONLY_OR_DEGREE = predicate(_IS_VALUE_ONLY_OR_DEGREE, "is_value_only(allow_degree)")
_SIMPLE_TEMP = predicate(_is_simple_temperature, "is_simple_temperature")

RULES: tuple[Rule, ...] = (
    Rule(
        name="integer (numeric)",
        pattern=(regex(r"-?\d+(\.\d+)?"),),
        prod=_prod_numeral_seed,
    ),
    Rule(
        name="number as temp",
        pattern=(predicate(is_numeral, "is_numeral"),),
        prod=_prod_numeral_as_temp,
    ),
    Rule(
        name="<latent temp> degrees",
        pattern=(_VALUE_ONLY, regex(r"(deg(ree?)?s?\.?)|°")),
        prod=_make_unit_rewriter(TemperatureUnit.DEGREE),
    ),
    Rule(
        name="<temp> Celsius",
        pattern=(_VALUE_ONLY_OR_DEGREE, regex(r"c(el[cs]?(ius)?)?\.?")),
        prod=_make_unit_rewriter(TemperatureUnit.CELSIUS),
    ),
    Rule(
        name="<temp> Fahrenheit",
        pattern=(_VALUE_ONLY_OR_DEGREE, regex(r"f(ah?rh?eh?n(h?eit)?)?\.?")),
        prod=_make_unit_rewriter(TemperatureUnit.FAHRENHEIT),
    ),
    Rule(
        name="<temp> below zero",
        pattern=(_VALUE_ONLY_OR_DEGREE, regex(r"below zero")),
        prod=_prod_below_zero,
    ),
    Rule(
        name="between|from <temp> and|to <temp>",
        pattern=(regex(r"between|from"), _SIMPLE_TEMP, regex(r"to|and"), _SIMPLE_TEMP),
        prod=_make_interval_prod(lo_idx=1, hi_idx=3),
    ),
    Rule(
        name="<temp> - <temp>",
        pattern=(_SIMPLE_TEMP, regex(r"-"), _SIMPLE_TEMP),
        prod=_make_interval_prod(lo_idx=0, hi_idx=2),
    ),
    Rule(
        name="over/above/at least/more than <temp>",
        pattern=(regex(r"over|above|at least|more than"), _SIMPLE_TEMP),
        prod=_make_open_interval_prod(TemperatureIntervalDirection.ABOVE),
    ),
    Rule(
        name="under/less/lower/no more than <temp>",
        pattern=(regex(r"under|(less|lower|not? more) than"), _SIMPLE_TEMP),
        prod=_make_open_interval_prod(TemperatureIntervalDirection.UNDER),
    ),
)
