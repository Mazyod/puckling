"""Arabic numeral rules — port of Duckling's `Numeral/AR/Rules.hs`."""

from __future__ import annotations

from puckling.dimensions.numeral.helpers import (
    add,
    parse_arabic_decimal,
    parse_arabic_int,
)
from puckling.dimensions.numeral.types import NumeralValue
from puckling.predicates import (
    is_multipliable,
    is_numeral,
    number_between,
    number_equal_to,
    one_of,
)
from puckling.types import Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# helpers

_WORD_BOUNDARY_LEFT = r"(?:(?<![\p{L}\p{N}_])|(?<=و))"
_WORD_BOUNDARY_RIGHT = r"(?![\p{L}\p{N}_])"
_NUMERIC_BOUNDARY_LEFT = r"(?<![\p{L}\p{N}_.,٫٬/+−])(?<!--)"
_NUMERIC_BOUNDARY_RIGHT = r"(?![\p{L}\p{N}_.,٫٬/+−-])"


def _word_re(pattern: str) -> str:
    """Prevent word numerals from matching inside larger Arabic words."""
    return rf"{_WORD_BOUNDARY_LEFT}(?:{pattern}){_WORD_BOUNDARY_RIGHT}"


def _numeric_re(pattern: str) -> str:
    return rf"{_NUMERIC_BOUNDARY_LEFT}(?:{pattern}){_NUMERIC_BOUNDARY_RIGHT}"


def _numeral(value: int | float, *, grain: int | None = None, multipliable: bool = False) -> Token:
    return Token(dim="numeral", value=NumeralValue(value=value, grain=grain, multipliable=multipliable))


def _value(t: Token) -> int | float | None:
    if t.dim != "numeral":
        return None
    v = getattr(t.value, "value", None)
    if isinstance(v, (int, float)):
        return v
    return None


def _is_numeral_without_grain(t: Token) -> bool:
    """Mirror Haskell `not . hasGrain`: numeral whose grain is None or <= 1."""
    if t.dim != "numeral":
        return False
    g = getattr(t.value, "grain", None)
    return not (isinstance(g, int) and g > 1)


def _decimals_to_double(x: int | float) -> float:
    """Mirror Haskell `decimalsToDouble`: 77 -> .77 by dividing by next power of 10."""
    if x == 0:
        return 0.0
    multiplier = 1
    for _ in range(10):
        if x - multiplier < 0:
            return float(x) / float(multiplier)
        multiplier *= 10
    return 0.0


# Map Arabic prefixes for tens (20..90); value = lookup * 10.
_DIGITS_MAP: dict[str, int] = {
    "عشر": 2,
    "ثلاث": 3,
    "اربع": 4,
    "أربع": 4,
    "خمس": 5,
    "ست": 6,
    "سبع": 7,
    "ثمان": 8,
    "تسع": 9,
}


# Word → (value, grain, multipliable) for `rulePowersOfTen`.
_POWERS_OF_TEN: dict[str, tuple[int, int, bool]] = {
    "مئة": (100, 2, True),
    "مئه": (100, 2, True),
    "مائة": (100, 2, True),
    "مائه": (100, 2, True),
    "مئتين": (200, 2, False),
    "مئتان": (200, 2, False),
    "مئات": (100, 2, True),
    "ألف": (1000, 3, True),
    "الف": (1000, 3, True),
    "الفين": (2000, 3, False),
    "الفان": (2000, 3, False),
    "الاف": (1000, 3, True),
    "آلاف": (1000, 3, True),
    "ملايين": (1_000_000, 6, True),
    "مليون": (1_000_000, 6, True),
    "مليونين": (2_000_000, 6, False),
    "مليونان": (2_000_000, 6, False),
}


# ---------------------------------------------------------------------------
# productions


def _prod_integer(value: int):
    def go(_toks: tuple[Token, ...]) -> Token | None:
        return _numeral(value)

    return go


def _prod_integer_20_90(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value.groups[0]
    if match is None:
        return None
    digit = _DIGITS_MAP.get(match)
    if digit is None:
        return None
    return _numeral(digit * 10)


def _prod_integer_13_19(tokens: tuple[Token, ...]) -> Token | None:
    v = _value(tokens[0])
    if v is None:
        return None
    return _numeral(v + 10)


def _prod_add_ignoring_middle(tokens: tuple[Token, ...]) -> Token | None:
    """Sum the first and third tokens, ignoring the regex token between them."""
    result = add(tokens[0], tokens[2])
    if result is None:
        return None
    return Token(dim="numeral", value=result)


def _prod_decimal_with_thousands_separator(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value.groups[0]
    if match is None:
        return None
    return _numeral(float(match.replace(",", "")))


def _prod_decimal_numeral(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value.groups[0]
    if match is None:
        return None
    text = match
    if text.startswith("."):
        text = "0" + text
    return _numeral(float(text))


def _prod_integer_with_thousands_separator(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value.groups[0]
    if match is None:
        return None
    return _numeral(float(match.replace(",", "")))


def _prod_integer_numeric(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value.groups[0]
    if match is None:
        return None
    return _numeral(parse_arabic_int(match))


def _prod_integer_numeric_ascii(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value.groups[0]
    if match is None:
        return None
    return _numeral(int(match))


def _prod_fractions_numeric(tokens: tuple[Token, ...]) -> Token | None:
    groups = tokens[0].value.groups
    if len(groups) < 2 or groups[0] is None or groups[1] is None:
        return None
    n = parse_arabic_int(groups[0])
    d = parse_arabic_int(groups[1])
    if d == 0:
        return None
    return _numeral(n / d)


def _prod_arabic_decimal(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value.groups[0]
    if match is None:
        return None
    return _numeral(parse_arabic_decimal(match))


def _prod_arabic_commas(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value.groups[0]
    if match is None:
        return None
    return _numeral(parse_arabic_decimal(match.replace("٬", "")))


def _prod_multiply(tokens: tuple[Token, ...]) -> Token | None:
    """Compose by multiplication: numeral * (multipliable numeral with grain).

    Mirrors Haskell `multiply`: when the right operand carries a grain, only
    succeeds if v2 > v1; the result inherits the right operand's grain.
    """
    a, b = _value(tokens[0]), _value(tokens[1])
    if a is None or b is None:
        return None
    grain = getattr(tokens[1].value, "grain", None)
    if grain is None:
        return _numeral(a * b)
    if b > a:
        return _numeral(a * b, grain=grain)
    return None


def _prod_numerals_prefix_minus(tokens: tuple[Token, ...]) -> Token | None:
    v = _value(tokens[1])
    if v is None:
        return None
    return _numeral(v * -1)


def _prod_numeral_dot_numeral(tokens: tuple[Token, ...]) -> Token | None:
    v1 = _value(tokens[0])
    v2 = _value(tokens[2])
    if v1 is None or v2 is None:
        return None
    return _numeral(v1 + _decimals_to_double(v2))


def _prod_powers_of_ten(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value.groups[0]
    if match is None:
        return None
    entry = _POWERS_OF_TEN.get(match.lower())
    if entry is None:
        return None
    value, grain, multipliable = entry
    return _numeral(value, grain=grain, multipliable=multipliable)


# ---------------------------------------------------------------------------
# rules


_rule_integer_0 = Rule(
    name="integer 0",
    pattern=(regex(_word_re(r"صفر")),),
    prod=_prod_integer(0),
)

_rule_integer_1 = Rule(
    name="integer 1",
    pattern=(regex(_word_re(r"واحد[ةه]?")),),
    prod=_prod_integer(1),
)

_rule_integer_2 = Rule(
    name="integer 2",
    pattern=(regex(_word_re(r"[إا]ثنت?[اي]ن")),),
    prod=_prod_integer(2),
)

_rule_integer_3 = Rule(
    name="integer 3",
    pattern=(regex(_word_re(r"(ثلاث[ةه]?)")),),
    prod=_prod_integer(3),
)

_rule_integer_4 = Rule(
    name="integer 4",
    pattern=(regex(_word_re(r"([أا]ربع[ةه]?)")),),
    prod=_prod_integer(4),
)

_rule_integer_5 = Rule(
    name="integer 5",
    pattern=(regex(_word_re(r"خمس[ةه]?")),),
    prod=_prod_integer(5),
)

_rule_integer_6 = Rule(
    name="integer 6",
    pattern=(regex(_word_re(r"ست[ةه]?")),),
    prod=_prod_integer(6),
)

_rule_integer_7 = Rule(
    name="integer 7",
    pattern=(regex(_word_re(r"سبع[ةه]?")),),
    prod=_prod_integer(7),
)

_rule_integer_8 = Rule(
    name="integer 8",
    pattern=(regex(_word_re(r"ثما??ني?[ةه]?")),),
    prod=_prod_integer(8),
)

_rule_integer_9 = Rule(
    name="integer 9",
    pattern=(regex(_word_re(r"تسع[ةه]?")),),
    prod=_prod_integer(9),
)

_rule_integer_10 = Rule(
    name="integer 10",
    pattern=(regex(_word_re(r"عشر[ةه]?")),),
    prod=_prod_integer(10),
)

_rule_integer_11 = Rule(
    name="integer 11",
    pattern=(regex(_word_re(r"([إاأ]حد[يى]? عشر[ةه]?)")),),
    prod=_prod_integer(11),
)

_rule_integer_12 = Rule(
    name="integer 12",
    pattern=(regex(_word_re(r"([إا]?ثن(ت)?[يىا] ?عشر[ةه]?)")),),
    prod=_prod_integer(12),
)

_rule_integer_13_19 = Rule(
    name="integer (13..19)",
    pattern=(
        predicate(number_between(3, 10), "between(3,10)"),
        predicate(number_equal_to(10), "==10"),
    ),
    prod=_prod_integer_13_19,
)

_rule_integer_20_90 = Rule(
    name="integer (20..90)",
    pattern=(regex(_word_re(r"(عشر|ثلاث|[أا]ربع|خمس|ست|سبع|ثمان|تسع)(ون|ين)")),),
    prod=_prod_integer_20_90,
)

_rule_integer_21_99 = Rule(
    name="integer 21..99",
    pattern=(
        predicate(number_between(1, 10), "between(1,10)"),
        regex(r"و"),
        predicate(one_of((20, 30, 40, 50, 60, 70, 80, 90)), "one_of(20..90)"),
    ),
    prod=_prod_add_ignoring_middle,
)

_rule_integer_101_999 = Rule(
    name="integer 101..999",
    pattern=(
        predicate(one_of((100, 200, 300, 400, 500, 600, 700, 800, 900)), "one_of(100..900)"),
        regex(r"و"),
        predicate(number_between(1, 100), "between(1,100)"),
    ),
    prod=_prod_add_ignoring_middle,
)

_rule_integer_200 = Rule(
    name="integer (200)",
    pattern=(regex(_word_re(r"مائتان|مائتين")),),
    prod=_prod_integer(200),
)

_rule_integer_300 = Rule(
    name="integer 300",
    pattern=(regex(_word_re(r"(ثلاث)ما?[ئي][ةه]")),),
    prod=_prod_integer(300),
)

_rule_integer_400 = Rule(
    name="integer 400",
    pattern=(regex(_word_re(r"([أا]ربع)ما?[ئي][ةه]")),),
    prod=_prod_integer(400),
)

_rule_integer_500 = Rule(
    name="integer 500",
    pattern=(regex(_word_re(r"(خمس)ما?[ئي][ةه]")),),
    prod=_prod_integer(500),
)

_rule_integer_600 = Rule(
    name="integer 600",
    pattern=(regex(_word_re(r"(ست)ما?[ئي][ةه]")),),
    prod=_prod_integer(600),
)

_rule_integer_700 = Rule(
    name="integer 700",
    pattern=(regex(_word_re(r"(سبع)ما?[ئي][ةه]")),),
    prod=_prod_integer(700),
)

_rule_integer_800 = Rule(
    name="integer 800",
    pattern=(regex(_word_re(r"(ثمان[ي]?)ما?[ئي][ةه]")),),
    prod=_prod_integer(800),
)

_rule_integer_900 = Rule(
    name="integer 900",
    pattern=(regex(_word_re(r"(تسع)ما?[ئي][ةه]")),),
    prod=_prod_integer(900),
)

_rule_decimal_with_thousands_separator = Rule(
    name="decimal with thousands separator",
    pattern=(regex(_numeric_re(r"([0-9]+(,[0-9][0-9][0-9])+\.[0-9]+)")),),
    prod=_prod_decimal_with_thousands_separator,
)

_rule_decimal_numeral = Rule(
    name="decimal number",
    pattern=(regex(_numeric_re(r"([0-9]*\.[0-9]+)")),),
    prod=_prod_decimal_numeral,
)

_rule_integer_with_thousands_separator = Rule(
    name="integer with thousands separator ,",
    pattern=(regex(_numeric_re(r"([0-9]{1,3}(,[0-9][0-9][0-9]){1,5})")),),
    prod=_prod_integer_with_thousands_separator,
)

_rule_integer_numeric = Rule(
    name="Arabic integer numeric",
    pattern=(regex(_numeric_re(r"([٠-٩]{1,18})")),),
    prod=_prod_integer_numeric,
)

# TODO(puckling): edge case — ASCII integer parsing belongs in the locale-agnostic
# `puckling.dimensions.numeral.rules` (mirroring upstream `Duckling/Numeral/Rules.hs`).
# Duplicated here so the AR corpus's plain-ASCII phrases ("100", "2000", ...) can
# resolve standalone; remove once the foundation provides the global rule.
_rule_integer_numeric_ascii = Rule(
    name="integer (numeric)",
    pattern=(regex(_numeric_re(r"([0-9]{1,18})")),),
    prod=_prod_integer_numeric_ascii,
)

_rule_fractions_numeric = Rule(
    name="Arabic fractional number numeric",
    pattern=(regex(_numeric_re(r"([٠-٩]+)/([٠-٩]+)")),),
    prod=_prod_fractions_numeric,
)

_rule_arabic_decimal = Rule(
    name="Arabic decimal number with Arabic decimal separator",
    pattern=(regex(_numeric_re(r"([٠-٩]*٫[٠-٩]+)")),),
    prod=_prod_arabic_decimal,
)

_rule_arabic_commas = Rule(
    name="Arabic number with commas and optional Arabic decimal separator",
    pattern=(regex(_numeric_re(r"([٠-٩]{1,3}(٬[٠-٩]{3}){1,5}(٫[٠-٩]+)?)")),),
    prod=_prod_arabic_commas,
)

_rule_multiply = Rule(
    name="compose by multiplication",
    pattern=(
        predicate(is_numeral, "is_numeral"),
        predicate(is_multipliable, "is_multipliable"),
    ),
    prod=_prod_multiply,
)

_rule_numerals_prefix_minus = Rule(
    name="numbers prefix with -, minus",
    pattern=(
        regex(r"(?<!-)-(?!\s*-)"),
        predicate(is_numeral, "is_numeral"),
    ),
    prod=_prod_numerals_prefix_minus,
)

_rule_numeral_dot_numeral = Rule(
    name="number dot number",
    pattern=(
        predicate(is_numeral, "is_numeral"),
        regex(_word_re(r"فاصل[ةه]")),
        predicate(_is_numeral_without_grain, "no_grain"),
    ),
    prod=_prod_numeral_dot_numeral,
)

_rule_powers_of_ten = Rule(
    name="powers of tens",
    pattern=(
        regex(
            _word_re(
                r"(ما?[ئي][ةه]|مئت(ان|ين)|مئات|[أا]لف(ان|ين)?|[آا]لاف|ملايين|مليون(ان|ين)?)"
            )
        ),
    ),
    prod=_prod_powers_of_ten,
)


RULES: tuple[Rule, ...] = (
    _rule_integer_numeric,
    _rule_integer_numeric_ascii,
    _rule_fractions_numeric,
    _rule_decimal_numeral,
    _rule_decimal_with_thousands_separator,
    _rule_integer_0,
    _rule_integer_7,
    _rule_integer_8,
    _rule_integer_9,
    _rule_integer_10,
    _rule_integer_11,
    _rule_integer_12,
    _rule_integer_13_19,
    _rule_integer_20_90,
    _rule_integer_1,
    _rule_integer_21_99,
    _rule_integer_101_999,
    _rule_integer_2,
    _rule_integer_3,
    _rule_integer_4,
    _rule_integer_5,
    _rule_integer_6,
    _rule_integer_300,
    _rule_integer_400,
    _rule_integer_500,
    _rule_integer_600,
    _rule_integer_700,
    _rule_integer_800,
    _rule_integer_900,
    _rule_integer_with_thousands_separator,
    _rule_multiply,
    _rule_numeral_dot_numeral,
    _rule_numerals_prefix_minus,
    _rule_powers_of_ten,
    _rule_integer_200,
    _rule_arabic_decimal,
    _rule_arabic_commas,
)
