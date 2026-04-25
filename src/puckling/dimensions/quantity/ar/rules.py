"""Arabic quantity rules — ported from Duckling/Quantity/AR/Rules.hs.

Covers cups, grams (with metric prefixes), pounds, and ounces, including dual
forms (كوبان/كوبين, أونصتان, …). Also surfaces ``<quantity> من <product>``.
"""

from __future__ import annotations

from collections.abc import Callable

from puckling.dimensions.numeral.helpers import parse_arabic_decimal, parse_arabic_int
from puckling.dimensions.numeral.types import NumeralValue
from puckling.dimensions.quantity.types import QuantityValue, quantity
from puckling.predicates import is_dim, is_positive
from puckling.types import RegexMatch, Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Numeric handling — keeps this rule file self-contained for AR. Mirrors
# Duckling's `Numeral.AR` integer/decimal rules just enough to feed the
# quantity grammar with a positive numeral token. The trailing `|\.\d+`
# extends the upstream-aligned core pattern to accept leading-dot decimals
# like ".75 كوب".

_NUMERIC_PATTERN = r"[٠-٩]+(٫[٠-٩]+)?|\d+(\.\d+)?|(?<!\d)\.\d+"


def _prod_numeric(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value
    if not isinstance(match, RegexMatch):
        return None
    text = match.text
    value: int | float = (
        parse_arabic_decimal(text) if ("." in text or "٫" in text) else parse_arabic_int(text)
    )
    return Token(dim="numeral", value=NumeralValue(value=value))


# Fractional literal: "3/4", "2/1000". Common in AR cooking quantities.
_FRACTION_PATTERN = r"(?<![\p{L}\p{N}])(\d+|[٠-٩]+)\s*/\s*(\d+|[٠-٩]+)(?![\p{L}\p{N}])"


def _prod_fraction(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value
    if not isinstance(match, RegexMatch):
        return None
    num_s, den_s = match.groups[0], match.groups[1]
    if num_s is None or den_s is None:
        return None
    num = parse_arabic_int(num_s)
    den = parse_arabic_int(den_s)
    if den == 0:
        return None
    return Token(dim="numeral", value=NumeralValue(value=num / den))


# ---------------------------------------------------------------------------
# Unit lexicon — boundary-protected so "غم" (gram) does not match inside
# "غمامة" (cloud) and friends. Each entry is (unit_name, pattern, ops_map).

# A scalar that the matched word multiplies the incoming numeral by. Mirrors
# Duckling's `opsMap`. Default for any unmatched alias is 1.
UnitOp = Callable[[float], float]


def _const(scale: float) -> UnitOp:
    def go(v: float) -> float:
        return v * scale

    return go


def _div(divisor: float) -> UnitOp:
    def go(v: float) -> float:
        return v / divisor

    return go


# Word-boundary helpers for Arabic + ASCII letters/digits. Plain `\b` is
# unreliable for Arabic in `regex`, so we explicitly forbid letters/digits
# on either side.
_BOUND_L = r"(?<![\p{L}\p{N}])"
_BOUND_R = r"(?![\p{L}\p{N}])"


def _bounded(pat: str) -> str:
    return _BOUND_L + r"(?:" + pat + r")" + _BOUND_R


# Cup: كوب / كوبان / كوبين / أكواب / اكواب.
_CUP_PATTERN = _bounded(r"كوب(?:ان|ين)?|[أا]كواب")
_CUP_OPS: dict[str, UnitOp] = {
    "كوبان": _const(2),
    "كوبين": _const(2),
}

# Pound: باوند / باوندان / باوندين.
_POUND_PATTERN = _bounded(r"باوند(?:ان|ين)?")
_POUND_OPS: dict[str, UnitOp] = {
    "باوندان": _const(2),
    "باوندين": _const(2),
}

# Ounce: أونصة / اونصة / أونصه / اونصه / أونصتان / اونصتان / أونصتين / اونصتين / أونصات / اونصات.
_OUNCE_PATTERN = _bounded(r"[أا]ونص(?:[ةه]|تان|تين|ات)")
_OUNCE_OPS: dict[str, UnitOp] = {
    "اونصتان": _const(2),
    "اونصتين": _const(2),
    "أونصتان": _const(2),
    "أونصتين": _const(2),
}

# Gram (with metric prefixes & abbreviations). Mirrors upstream's combined
# regex but written in long form for readability.
_GRAM_PATTERN = _bounded(
    r"(?:(?:كيلو|مي?لي?)\s?)?(?:[غج]رام(?:ات|ين|ان)?)"  # full forms with optional milli/kilo
    r"|ك[غج]م?"  # كغ / كغم / كج / كجم
    r"|مل[غج]"  # ملغ / ملج
    r"|[غج]م"  # غم / جم
)


def _gram_ops() -> dict[str, UnitOp]:
    """Return the gram ops table — every alias maps to a scaling fn."""
    ops: dict[str, UnitOp] = {}
    # Dual forms → * 2 (base gram).
    for w in ("غرامان", "غرامين", "جرامان", "جرامين"):
        ops[w] = _const(2)
    # ميلي + dual → / 500 (i.e. 2 / 1000).
    for w in (
        "ميلي غرامان",
        "ميليغرامان",
        "ميلغرامان",
        "ميلي غرامين",
        "ميليغرامين",
        "ميلغرامين",
        "ميلي جرامان",
        "ميليجرامان",
        "ميلجرامان",
        "ميلي جرامين",
        "ميليجرامين",
        "ميلجرامين",
    ):
        ops[w] = _div(500)
    # Milligram singular/plural → / 1000.
    for w in (
        "ميلي غرام",
        "ميليغرام",
        "ميلغرام",
        "ميلي غرامات",
        "ميليغرامات",
        "ميلغرامات",
        "ميلي جرام",
        "ميليجرام",
        "ملج",
        "ميلجرام",
        "ميلي جرامات",
        "ميليجرامات",
        "ميلجرامات",
        "ملغ",
    ):
        ops[w] = _div(1000)
    # Kilogram singular/plural → * 1000.
    for w in (
        "كيلوغرام",
        "كيلو غرام",
        "كيلوغرامات",
        "كيلو غرامات",
        "كيلوجرام",
        "كيلو جرام",
        "كيلوجرامات",
        "كيلو جرامات",
        "كغ",
        "كغم",
        "كج",
        "كجم",
    ):
        ops[w] = _const(1000)
    # Kilogram dual → * 2000.
    for w in (
        "كيلوغرامان",
        "كيلوغرامين",
        "كيلو غرامان",
        "كيلو غرامين",
        "كيلوجرامان",
        "كيلوجرامين",
        "كيلو جرامان",
        "كيلو جرامين",
    ):
        ops[w] = _const(2000)
    return ops


_GRAM_OPS = _gram_ops()


# All four units, in (display name, regex, base unit, ops) form.
_UNITS: tuple[tuple[str, str, str, dict[str, UnitOp]], ...] = (
    ("cups", _CUP_PATTERN, "cup", _CUP_OPS),
    ("grams", _GRAM_PATTERN, "gram", _GRAM_OPS),
    ("pounds", _POUND_PATTERN, "pound", _POUND_OPS),
    ("ounces", _OUNCE_PATTERN, "ounce", _OUNCE_OPS),
)


def _apply_op(ops: dict[str, UnitOp], match_text: str, value: float) -> float:
    """Apply the alias-specific scale (if any) to ``value``."""
    op = ops.get(match_text)
    return op(value) if op is not None else value


def _build_numeral_unit_rule(name: str, pattern: str, unit: str, ops: dict[str, UnitOp]) -> Rule:
    """Numeral followed by a unit word — e.g. "2 غرام" or "0.5 كيلوجرام"."""

    def prod(tokens: tuple[Token, ...]) -> Token | None:
        num_tok, unit_tok = tokens
        match = unit_tok.value
        if not isinstance(match, RegexMatch):
            return None
        scaled = _apply_op(ops, match.text, float(num_tok.value.value))
        return Token(dim="quantity", value=quantity(scaled, unit))

    return Rule(
        name=f"<quantity> {name}",
        pattern=(predicate(is_positive, "is_positive_numeral"), regex(pattern)),
        prod=prod,
    )


def _build_standalone_unit_rule(name: str, pattern: str, unit: str, ops: dict[str, UnitOp]) -> Rule:
    """Bare unit word with implicit value 1 — e.g. "كيلوغرام" → 1000 g, "كوبان" → 2 cups."""

    def prod(tokens: tuple[Token, ...]) -> Token | None:
        match = tokens[0].value
        if not isinstance(match, RegexMatch):
            return None
        scaled = _apply_op(ops, match.text, 1.0)
        return Token(dim="quantity", value=quantity(scaled, unit))

    return Rule(
        name=f"a {name}",
        pattern=(regex(pattern),),
        prod=prod,
    )


# <quantity> من <product>: e.g. "500 غرام من الفراولة" → quantity with product="الفراولة".
_PRODUCT_PATTERN = r"من\s+([ء-ي]+)"


def _prod_quantity_of_product(tokens: tuple[Token, ...]) -> Token | None:
    qty_tok, prod_tok = tokens
    qv = qty_tok.value
    pm = prod_tok.value
    if not isinstance(qv, QuantityValue) or not isinstance(pm, RegexMatch):
        return None
    product = pm.groups[0]
    if not product:
        return None
    return Token(dim="quantity", value=quantity(qv.value, qv.unit, product=product))


# ---------------------------------------------------------------------------
# Assembled RULES tuple.

_NUMERIC_RULE = Rule(
    name="integer (numeric AR)",
    pattern=(regex(_NUMERIC_PATTERN),),
    prod=_prod_numeric,
)

_FRACTION_RULE = Rule(
    name="fractional numeric AR",
    pattern=(regex(_FRACTION_PATTERN),),
    prod=_prod_fraction,
)

_QUANTITY_OF_PRODUCT_RULE = Rule(
    name="<quantity> of product",
    pattern=(predicate(is_dim("quantity"), "is_quantity"), regex(_PRODUCT_PATTERN)),
    prod=_prod_quantity_of_product,
)


def _build_rules() -> tuple[Rule, ...]:
    rules: list[Rule] = [_NUMERIC_RULE, _FRACTION_RULE, _QUANTITY_OF_PRODUCT_RULE]
    for name, pat, unit, ops in _UNITS:
        rules.append(_build_numeral_unit_rule(name, pat, unit, ops))
        rules.append(_build_standalone_unit_rule(name, pat, unit, ops))
    return tuple(rules)


RULES: tuple[Rule, ...] = _build_rules()
