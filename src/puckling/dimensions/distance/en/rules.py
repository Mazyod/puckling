"""Distance EN rules — port of `Duckling/Distance/EN/Rules.hs`.

Includes:
  * a numeric-helper seeder so simple "<n> <unit>" matches don't depend on the
    Numeral EN dimension (which is built in a separate worker),
  * per-unit "<numeral> <unit>" rules,
  * local boundary/context guards to avoid surfacing embedded units or partial
    values from unsupported range/open-interval forms,
  * a precision wrapper ("about|exactly <dist>"),
  * composite distance summation with comma/"and" or adjacency, including
    cross-system reconciliation that prefers the metric system.

Rules that require interval-/min-/max-shaped distance values (between, under,
over) and the ambiguous "M" unit from upstream are intentionally omitted —
the foundation `DistanceValue` only carries `value` + `unit`.
"""

from __future__ import annotations

from puckling.dimensions.distance.types import DistanceUnit, DistanceValue
from puckling.dimensions.numeral.types import NumeralValue
from puckling.predicates import is_numeral
from puckling.types import Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Numeric seed — Numeral EN ships in a separate worker, so we surface a tiny
# digit/decimal token here. It never wins on its own; the per-unit rules below
# always consume it into a richer distance token.

_NUMERIC_RE = r"(?<![\p{L}\p{N}_./-])\d+(\.\d+)?"
_NUMERIC_CONTEXT_RE = r"\d+(?:\.\d+)?"


def _prod_numeric(tokens: tuple[Token, ...]) -> Token | None:
    text = tokens[0].value.text
    value: int | float = float(text) if "." in text else int(text)
    return Token(dim="numeral", value=NumeralValue(value=value))


_rule_numeric_seed = Rule(
    name="<numeric>",
    pattern=(regex(_NUMERIC_RE),),
    prod=_prod_numeric,
)


# ---------------------------------------------------------------------------
# Per-unit "<numeral> <unit>" rules


def _is_distance_token(t: Token) -> bool:
    if t.dim != "distance":
        return False
    v = t.value
    return (
        isinstance(v, DistanceValue)
        and v.unit is not None
        and v.value is not None
    )


_UNIT_LEFT_GUARD = (
    rf"(?<![\p{{L}}_/]{_NUMERIC_CONTEXT_RE}\s*)"
    rf"(?<![-–—]\s*{_NUMERIC_CONTEXT_RE}\s*)"
)
_UNSUPPORTED_DISTANCE_SHAPE_GUARD = (
    rf"(?<!\b{_NUMERIC_CONTEXT_RE}\s*[-–—/]\s*{_NUMERIC_CONTEXT_RE}\s*)"
    rf"(?<!\b{_NUMERIC_CONTEXT_RE}\s+to\s+{_NUMERIC_CONTEXT_RE}\s*)"
    rf"(?<!\bfrom\s+{_NUMERIC_CONTEXT_RE}\s*[^\s\d]+\s+to\s+{_NUMERIC_CONTEXT_RE}\s*)"
    rf"(?<!\bbetween\s+{_NUMERIC_CONTEXT_RE}\s+and\s+{_NUMERIC_CONTEXT_RE}\s*)"
    rf"(?<!\b(?:under|below|less\s+than|not\s+more\s+than|no\s+more\s+than|"
    rf"over|above|at\s+least|more\s+than)\s+{_NUMERIC_CONTEXT_RE}\s*)"
)
_UNSUPPORTED_DISTANCE_SHAPE_RIGHT_GUARD = (
    rf"(?!\s*(?:[-–—]|to\b)\s*{_NUMERIC_CONTEXT_RE})"
)
_UNIT_RIGHT_GUARD = r"(?![\p{L}\p{N}_/])"


def _guarded_unit_pattern(pattern_re: str) -> str:
    return (
        f"{_UNIT_LEFT_GUARD}"
        f"{_UNSUPPORTED_DISTANCE_SHAPE_GUARD}"
        f"(?:{pattern_re})"
        f"{_UNSUPPORTED_DISTANCE_SHAPE_RIGHT_GUARD}"
        f"{_UNIT_RIGHT_GUARD}"
    )


def _make_unit_rule(name: str, pattern_re: str, unit: DistanceUnit) -> Rule:
    def prod(tokens: tuple[Token, ...]) -> Token | None:
        n = tokens[0].value.value
        if not isinstance(n, (int, float)) or isinstance(n, bool):
            return None
        return Token(dim="distance", value=DistanceValue(value=n, unit=unit))

    return Rule(
        name=name,
        pattern=(
            predicate(is_numeral, "is_numeral"),
            regex(_guarded_unit_pattern(pattern_re)),
        ),
        prod=prod,
    )


# (rule name, regex, unit). Mirrors upstream `distances` minus the ambiguous
# "m" unit — `DistanceValue` has no `M` analogue.
_UNIT_TABLE: tuple[tuple[str, str, DistanceUnit], ...] = (
    # Imperial
    ("<numeral> miles", r"mi(le(s)?)?", DistanceUnit.MILE),
    ("<numeral> yards", r"y(ar)?ds?", DistanceUnit.YARD),
    ("<numeral> feet", r"('|f(oo|ee)?ts?)", DistanceUnit.FOOT),
    ("<numeral> inches", r"(\"|''|in(ch(es)?)?)", DistanceUnit.INCH),
    # Metric
    ("<numeral> km", r"k(ilo)?m?(et(er|re))?s?", DistanceUnit.KILOMETRE),
    ("<numeral> meters", r"met(er|re)s?", DistanceUnit.METRE),
    ("<numeral> centimeters", r"cm|centimet(er|re)s?", DistanceUnit.CENTIMETRE),
    ("<numeral> millimeters", r"mm|millimet(er|re)s?", DistanceUnit.MILLIMETRE),
)

_unit_rules: tuple[Rule, ...] = tuple(
    _make_unit_rule(name, pat, unit) for (name, pat, unit) in _UNIT_TABLE
)


# ---------------------------------------------------------------------------
# Precision wrapper: "about|exactly <dist>"


def _prod_precision(tokens: tuple[Token, ...]) -> Token | None:
    return tokens[1]


_rule_precision = Rule(
    name="about|exactly <dist>",
    pattern=(
        regex(r"exactly|precisely|about|approx(\.|imately)?|close to|near( to)?|around|almost"),
        predicate(_is_distance_token, "is_simple_distance"),
    ),
    prod=_prod_precision,
)


# ---------------------------------------------------------------------------
# Composite distance summation
#
# Upstream `distanceSum` reconciles two values across measurement systems:
#   * mixed metric/imperial → result is in the metric unit,
#   * same system → result is in the smaller of the two units.

_METRIC_UNITS = {
    DistanceUnit.KILOMETRE,
    DistanceUnit.METRE,
    DistanceUnit.CENTIMETRE,
    DistanceUnit.MILLIMETRE,
}

# Multiplicative factors to a system's smallest unit. Staying integer-valued
# inside each measurement system keeps composite sums exact (no 0.01 divide).
_TO_MM: dict[DistanceUnit, int] = {
    DistanceUnit.MILLIMETRE: 1,
    DistanceUnit.CENTIMETRE: 10,
    DistanceUnit.METRE: 1000,
    DistanceUnit.KILOMETRE: 1_000_000,
}
_TO_INCHES: dict[DistanceUnit, int] = {
    DistanceUnit.INCH: 1,
    DistanceUnit.FOOT: 12,
    DistanceUnit.YARD: 36,
    DistanceUnit.MILE: 63360,
}

# Smaller unit comes first; used to pick the preferred unit when both operands
# share a measurement system.
_METRIC_ORDER: tuple[DistanceUnit, ...] = (
    DistanceUnit.MILLIMETRE,
    DistanceUnit.CENTIMETRE,
    DistanceUnit.METRE,
    DistanceUnit.KILOMETRE,
)
_IMPERIAL_ORDER: tuple[DistanceUnit, ...] = (
    DistanceUnit.INCH,
    DistanceUnit.FOOT,
    DistanceUnit.YARD,
    DistanceUnit.MILE,
)
_METRES_PER_INCH = 0.0254


def _smaller_in_order(order: tuple[DistanceUnit, ...], a: DistanceUnit, b: DistanceUnit) -> DistanceUnit:
    return a if order.index(a) <= order.index(b) else b


def _sum_same_system(
    v1: float, u1: DistanceUnit, v2: float, u2: DistanceUnit,
    factors: dict[DistanceUnit, int], order: tuple[DistanceUnit, ...],
) -> tuple[float, DistanceUnit]:
    # Compose in the smallest unit then divide once at the target factor —
    # within a system every factor divides the next, so an integer-valued
    # input round-trips exactly.
    target = _smaller_in_order(order, u1, u2)
    summed = (v1 * factors[u1] + v2 * factors[u2]) / factors[target]
    return summed, target


def _sum_mixed(
    v1: float, u1: DistanceUnit, v2: float, u2: DistanceUnit,
) -> tuple[float, DistanceUnit]:
    # Mixed-system: prefer the metric unit, convert imperial via metres.
    if u1 in _METRIC_UNITS:
        metric_v, metric_u = v1, u1
        imp_v, imp_u = v2, u2
    else:
        metric_v, metric_u = v2, u2
        imp_v, imp_u = v1, u1
    metric_in_mm = metric_v * _TO_MM[metric_u]
    imperial_in_mm = imp_v * _TO_INCHES[imp_u] * _METRES_PER_INCH * 1000
    summed_mm = metric_in_mm + imperial_in_mm
    return summed_mm / _TO_MM[metric_u], metric_u


def _distance_sum(
    v1: float, u1: DistanceUnit, v2: float, u2: DistanceUnit
) -> DistanceValue | None:
    if u1 == u2:
        return None
    metric1 = u1 in _METRIC_UNITS
    metric2 = u2 in _METRIC_UNITS
    if metric1 and metric2:
        summed, target = _sum_same_system(v1, u1, v2, u2, _TO_MM, _METRIC_ORDER)
    elif (not metric1) and (not metric2):
        summed, target = _sum_same_system(v1, u1, v2, u2, _TO_INCHES, _IMPERIAL_ORDER)
    else:
        summed, target = _sum_mixed(v1, u1, v2, u2)
    # Collapse trivially-integer floats so corpus comparisons that expect
    # plain ints (e.g. 94, 13, 166, 1000806) succeed exactly.
    if isinstance(summed, float) and summed.is_integer():
        summed = int(summed)
    return DistanceValue(value=summed, unit=target)


def _combine_distances(left: Token, right: Token) -> Token | None:
    v1, u1 = left.value.value, left.value.unit
    v2, u2 = right.value.value, right.value.unit
    if not (isinstance(v1, (int, float)) and isinstance(v2, (int, float))):
        return None
    if v1 <= 0 or v2 <= 0 or u1 is None or u2 is None or u1 == u2:
        return None
    summed = _distance_sum(float(v1), u1, float(v2), u2)
    if summed is None:
        return None
    return Token(dim="distance", value=summed)


def _prod_composite_separator(tokens: tuple[Token, ...]) -> Token | None:
    return _combine_distances(tokens[0], tokens[2])


def _prod_composite_adjacent(tokens: tuple[Token, ...]) -> Token | None:
    return _combine_distances(tokens[0], tokens[1])


_rule_composite_separator = Rule(
    name="composite <distance> (with ,/and)",
    pattern=(
        predicate(_is_distance_token, "is_simple_distance"),
        regex(r",|and"),
        predicate(_is_distance_token, "is_simple_distance"),
    ),
    prod=_prod_composite_separator,
)

_rule_composite_adjacent = Rule(
    name="composite <distance>",
    pattern=(
        predicate(_is_distance_token, "is_simple_distance"),
        predicate(_is_distance_token, "is_simple_distance"),
    ),
    prod=_prod_composite_adjacent,
)


# ---------------------------------------------------------------------------
# RULES export

RULES: tuple[Rule, ...] = (
    _rule_numeric_seed,
    *_unit_rules,
    _rule_precision,
    _rule_composite_separator,
    _rule_composite_adjacent,
)
