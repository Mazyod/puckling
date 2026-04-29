"""Quantity rules for English.

Ported from Duckling/Quantity/EN/Rules.hs. Captures phrases like
"2 cups", "two cups of flour", "a pound", and "3 grams of sugar".

Scope: numeral + unit (cup / gram / pound / ounce), with optional
"of <product>" suffix and an "a/an <unit>" shortcut. Interval phrasing
("between 2 and 5 cups"), precision modifiers ("about", "almost"), and
unit conversion (kg/mg -> gram) are intentionally out-of-scope here and
marked TODO; upstream handles them with helpers we have not ported yet.
"""

from __future__ import annotations

from puckling.dimensions.numeral.types import NumeralValue
from puckling.dimensions.quantity.types import QuantityValue, quantity
from puckling.predicates import is_positive
from puckling.types import Rule, Token, predicate, regex

# Surface form (regex) -> singular surface form (regex) -> canonical unit string.
_UNITS: tuple[tuple[str, str, str, str], ...] = (
    ("cup", r"cups?", r"cup", "cup"),
    ("gram", r"g(?:ram)?s?\.?", r"g(?:ram)?\.?", "gram"),
    ("pound", r"(?:lb|pound)s?", r"(?:lb|pound)", "pound"),
    ("ounce", r"(?:ounces?|oz)", r"(?:ounce|oz)", "ounce"),
)

_BOUND_L = r"(?<![\p{L}\p{N}.,+-])"
_BOUND_R = r"(?![\p{L}\p{N}]|[./-][\p{L}])"


def _bounded(pattern: str) -> str:
    return _BOUND_L + r"(?:" + pattern + r")" + _BOUND_R


def _digit_prod(tokens: tuple[Token, ...]) -> Token | None:
    """Emit a numeral token for any decimal literal in source text.

    This keeps the Quantity unit self-contained: tests don't need the
    full Numeral grammar to exercise "2 cups". Whole-grammar parses get
    the same numeral from upstream Numeral rules; the engine dedupes
    identical (dim, range, value) tokens.
    """
    text = tokens[0].value.text
    if "." in text:
        # Handle bare ".75" → 0.75 (Python float() accepts this) and "2."
        value: int | float = float(text)
    else:
        value = int(text)
    return Token(dim="numeral", value=NumeralValue(value=value))


_RULE_DIGITS = Rule(
    name="integer/decimal (quantity-local)",
    # Matches "2", "2.5", "0.75", and the bare-leading-dot ".75".
    pattern=(regex(_bounded(r"\d+(?:\.\d+)?|\.\d+")),),
    prod=_digit_prod,
)


def _make_numeral_unit_rule(name: str, unit_regex: str, unit: str) -> Rule:
    """Build a `<numeral> <unit>` rule for one canonical unit."""

    def prod(tokens: tuple[Token, ...]) -> Token | None:
        n = tokens[0].value.value
        return Token(dim="quantity", value=quantity(float(n), unit))

    return Rule(
        name=f"<numeral> {name}",
        pattern=(predicate(is_positive, "is_positive"), regex(unit_regex)),
        prod=prod,
    )


def _make_a_unit_rule(name: str, unit_regex: str, unit: str) -> Rule:
    """Build an `a|an <unit>` rule (e.g. "a cup", "an ounce")."""

    def prod(_tokens: tuple[Token, ...]) -> Token | None:
        return Token(dim="quantity", value=quantity(1.0, unit))

    return Rule(
        name=f"a {name}",
        pattern=(regex(rf"an?\s+{unit_regex}"),),
        prod=prod,
    )


def _quantity_of_product_prod(tokens: tuple[Token, ...]) -> Token | None:
    """Attach a product to an existing quantity token: '2 cups of flour'."""
    qty: QuantityValue = tokens[0].value
    # Don't re-attach: keeps "2 cups of flour of cake" from collapsing weirdly.
    if qty.product is not None:
        return None
    if tokens[1].range.start == tokens[0].range.end:
        return None
    product_match = tokens[1].value.groups[0]
    if product_match is None:
        return None
    return Token(
        dim="quantity",
        value=QuantityValue(value=qty.value, unit=qty.unit, product=product_match.lower()),
    )


def _is_quantity(t: Token) -> bool:
    return t.dim == "quantity"


_RULE_QUANTITY_OF_PRODUCT = Rule(
    name="<quantity> of <product>",
    pattern=(
        predicate(_is_quantity, "is_quantity"),
        regex(r"of\s+([\p{L}][\p{L}'-]*)(?![\p{L}\p{N}])"),
    ),
    prod=_quantity_of_product_prod,
)


# TODO(puckling): edge case — interval forms ("between X and Y", "X-Y",
#   "less than X", "more than X") are upstream but require a richer
#   QuantityValue (min/max/interval) we haven't modelled yet.
# TODO(puckling): edge case — precision modifiers ("about", "around",
#   "approximately") are dropped here; upstream forwards the wrapped value.
# TODO(puckling): edge case — kilogram/milligram conversion to grams.
#   Upstream's opsMap multiplies/divides the numeric value by 1000.

RULES: tuple[Rule, ...] = (
    _RULE_DIGITS,
    _RULE_QUANTITY_OF_PRODUCT,
    *(
        _make_numeral_unit_rule(name, _bounded(rx), unit)
        for name, rx, _singular_rx, unit in _UNITS
    ),
    *(
        _make_a_unit_rule(name, _bounded(singular_rx), unit)
        for name, _rx, singular_rx, unit in _UNITS
    ),
)
