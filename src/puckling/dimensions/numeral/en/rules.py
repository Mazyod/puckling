"""English Numeral rules — ported from `Duckling/Numeral/EN/Rules.hs`."""

from __future__ import annotations

from puckling.dimensions.numeral.types import NumeralValue
from puckling.predicates import is_multipliable, is_numeral, is_positive
from puckling.types import Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Lookup tables (mirrors the Haskell `HashMap`s)

_ZERO_NINETEEN: dict[str, int] = {
    "naught": 0,
    "nil": 0,
    "nought": 0,
    "none": 0,
    "zero": 0,
    "zilch": 0,
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
}

_INFORMAL: dict[str, int] = {
    "single": 1,
    "a couple": 2,
    "a couple of": 2,
    "couple": 2,
    "couples": 2,
    "couple of": 2,
    "couples of": 2,
    "a pair": 2,
    "a pair of": 2,
    "pair": 2,
    "pairs": 2,
    "pair of": 2,
    "pairs of": 2,
    "a few": 3,
    "few": 3,
}

_TENS: dict[str, int] = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fourty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

_POWERS_OF_TEN: dict[str, int] = {
    "hundred": 2,
    "thousand": 3,
    "lakh": 5,
    "lkh": 5,
    "l": 5,
    "lac": 5,
    "million": 6,
    "cr": 7,
    "crore": 7,
    "krore": 7,
    "kr": 7,
    "koti": 7,
    "billion": 9,
    "trillion": 12,
}


# ---------------------------------------------------------------------------
# Local predicate helpers (faithful to upstream semantics)


def _is_positive_or_zero(t: Token) -> bool:
    """Mirror Haskell's `isPositive`: numeral with value >= 0."""
    if t.dim != "numeral":
        return False
    v = getattr(t.value, "value", None)
    return isinstance(v, (int, float)) and v >= 0


def _has_grain_positive(t: Token) -> bool:
    """Mirror Haskell `hasGrain & isPositive`: grain > 1 and value >= 0."""
    if not _is_positive_or_zero(t):
        return False
    g = getattr(t.value, "grain", None)
    return isinstance(g, int) and g > 1


def _not_multipliable_positive(t: Token) -> bool:
    return _is_positive_or_zero(t) and not is_multipliable(t)


def _is_integer_positive(t: Token) -> bool:
    if t.dim != "numeral":
        return False
    v = getattr(t.value, "value", None)
    if not isinstance(v, (int, float)) or v <= 0:
        return False
    return isinstance(v, int) or v.is_integer()


_TENS_VALUES = frozenset({20, 30, 40, 50, 60, 70, 80, 90})


def _is_tens_20_90(t: Token) -> bool:
    if t.dim != "numeral" or is_multipliable(t):
        return False
    return getattr(t.value, "value", None) in _TENS_VALUES


def _is_units_1_9(t: Token) -> bool:
    if t.dim != "numeral" or is_multipliable(t):
        return False
    v = getattr(t.value, "value", None)
    return isinstance(v, (int, float)) and 1 <= v < 10


def _no_grain(t: Token) -> bool:
    """Mirror Haskell `not hasGrain`: True for numerals without grain or with grain <= 1."""
    if t.dim != "numeral":
        return False
    g = getattr(t.value, "grain", None)
    return g is None or (isinstance(g, int) and g <= 1)


# ---------------------------------------------------------------------------
# Numeric helpers


def _decimals_to_double(x: float) -> float:
    """`77 -> .77`. Find the smallest power of ten greater than `x`, divide."""
    multiplier = 1.0
    for _ in range(10):
        if x - multiplier < 0:
            return x / multiplier
        multiplier *= 10
    return 0.0


def _numeral_token(value: int | float, *, grain: int | None = None, multipliable: bool = False) -> Token:
    return Token(dim="numeral", value=NumeralValue(value=value, grain=grain, multipliable=multipliable))


def _multiply(left: Token, right: Token) -> Token | None:
    """Mirror Haskell `multiply`: keep grain when `v2 > v1`, else fail.

    Note: `multipliable` is False on the result; only `withMultipliable` toggles
    it, and `multiply` doesn't call it.
    """
    v1 = getattr(left.value, "value", None)
    v2 = getattr(right.value, "value", None)
    if not isinstance(v1, (int, float)) or not isinstance(v2, (int, float)):
        return None
    g = getattr(right.value, "grain", None)
    if g is None:
        return _numeral_token(v1 * v2)
    if v2 > v1:
        return _numeral_token(v1 * v2, grain=g, multipliable=False)
    return None


# ---------------------------------------------------------------------------
# Rule productions


def _prod_dozen(_tokens: tuple[Token, ...]) -> Token | None:
    return _numeral_token(12, multipliable=True)


def _prod_to_nineteen(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value.groups[0]
    if match is None:
        return None
    key = match.lower()
    val = _ZERO_NINETEEN.get(key, _INFORMAL.get(key))
    if val is None:
        return None
    return _numeral_token(val)


def _prod_tens(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value.groups[0]
    if match is None:
        return None
    val = _TENS.get(match.lower())
    if val is None:
        return None
    return _numeral_token(val)


def _prod_powers_of_ten(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value.groups[0]
    if match is None:
        return None
    grain = _POWERS_OF_TEN.get(match.lower())
    if grain is None:
        return None
    return _numeral_token(float(10**grain), grain=grain, multipliable=True)


def _prod_composite_tens(tokens: tuple[Token, ...]) -> Token | None:
    """Sum of tens (20..90) and units (1..9). Engine-skipped whitespace is OK;
    the optional dash slot, when present, sits between."""
    tens = tokens[0].value.value
    # The middle token is either a regex match (the dash) or the units token.
    units = tokens[-1].value.value
    return _numeral_token(tens + units)


def _prod_skip_hundreds_1(tokens: tuple[Token, ...]) -> Token | None:
    m1 = tokens[0].value.groups[0]
    m2 = tokens[1].value.groups[0]
    if m1 is None or m2 is None:
        return None
    x1 = m1.lower()
    x2 = m2.lower()
    if x1 not in _ZERO_NINETEEN:
        return None
    rest = _ZERO_NINETEEN.get(x2)
    if rest is None:
        rest = _TENS.get(x2)
    if rest is None:
        return None
    return _numeral_token(_ZERO_NINETEEN[x1] * 100 + rest)


def _prod_skip_hundreds_2(tokens: tuple[Token, ...]) -> Token | None:
    m1 = tokens[0].value.groups[0]
    m2 = tokens[1].value.groups[0]
    m3 = tokens[2].value.groups[0]
    if m1 is None or m2 is None or m3 is None:
        return None
    x1 = m1.lower()
    x2 = m2.lower()
    x3 = m3.lower()
    if x1 not in _ZERO_NINETEEN or x2 not in _TENS or x3 not in _ZERO_NINETEEN:
        return None
    return _numeral_token(_ZERO_NINETEEN[x1] * 100 + _TENS[x2] + _ZERO_NINETEEN[x3])


def _prod_dot_spelled_out(tokens: tuple[Token, ...]) -> Token | None:
    v1 = tokens[0].value.value
    v2 = tokens[2].value.value
    return _numeral_token(float(v1) + _decimals_to_double(float(v2)))


def _prod_leading_dot_spelled_out(tokens: tuple[Token, ...]) -> Token | None:
    v = tokens[1].value.value
    return _numeral_token(_decimals_to_double(float(v)))


def _prod_decimals(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value.groups[0]
    if match is None:
        return None
    return _numeral_token(float(match))


def _prod_commas(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value.groups[0]
    if match is None:
        return None
    cleaned = match.replace(",", "")
    return _numeral_token(float(cleaned))


def _prod_suffixes(tokens: tuple[Token, ...]) -> Token | None:
    nd = tokens[0].value
    match = tokens[1].value.groups[0]
    if match is None:
        return None
    multiplier = {"k": 1e3, "m": 1e6, "g": 1e9}.get(match.lower())
    if multiplier is None:
        return None
    return _numeral_token(float(nd.value) * multiplier)


def _prod_negative(tokens: tuple[Token, ...]) -> Token | None:
    return _numeral_token(-float(tokens[1].value.value))


def _prod_sum(tokens: tuple[Token, ...]) -> Token | None:
    nd1 = tokens[0].value
    nd2 = tokens[-1].value
    g = getattr(nd1, "grain", None)
    if not isinstance(g, int):
        return None
    if (10**g) <= nd2.value:
        return None
    return _numeral_token(float(nd1.value) + float(nd2.value))


def _prod_multiply(tokens: tuple[Token, ...]) -> Token | None:
    return _multiply(tokens[0], tokens[1])


def _prod_legal_parens(tokens: tuple[Token, ...]) -> Token | None:
    n1 = tokens[0].value.value
    n2 = tokens[2].value.value
    if n1 != n2:
        return None
    return _numeral_token(float(n1))


def _prod_integer_numeric(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value.groups[0]
    if match is None:
        return None
    return _numeral_token(int(match))


def _prod_fractional(tokens: tuple[Token, ...]) -> Token | None:
    n_text = tokens[0].value.groups[0]
    d_text = tokens[0].value.groups[1]
    if n_text is None or d_text is None:
        return None
    denominator = float(d_text)
    if denominator == 0:
        return None
    return _numeral_token(float(n_text) / denominator)


# ---------------------------------------------------------------------------
# RULES

_TO_NINETEEN_RE = (
    r"\b(none|zilch|naught|nought|nil|zero|one|single|two|"
    r"(a )?(pair|couple)s?( of)?|three|(a )?few|"
    r"fourteen|four|fifteen|five|sixteen|six|seventeen|seven|"
    r"eighteen|eight|nineteen|nine|ten|eleven|twelve|thirteen)\b"
)

_TENS_RE = r"\b(twenty|thirty|fou?rty|fifty|sixty|seventy|eighty|ninety)\b"

_POWERS_OF_TEN_RE = r"\b(hundred|thousand|l(ac|(a?kh)?)|million|((k|c)r(ore)?|koti)|billion)s?\b"

_ONE_NINE_RE = r"\b(one|two|three|four|five|six|seven|eight|nine)\b"

_TEN_NINETY_RE = (
    r"\b(ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
    r"eighteen|nineteen|twenty|thirty|fou?rty|fifty|sixty|seventy|"
    r"eighty|ninety)\b"
)


RULES: tuple[Rule, ...] = (
    Rule(
        name="integer (numeric)",
        pattern=(regex(r"(\d{1,18})"),),
        prod=_prod_integer_numeric,
    ),
    Rule(
        name="fractional number",
        pattern=(regex(r"(\d+)/(\d+)"),),
        prod=_prod_fractional,
    ),
    Rule(
        name="integer (0..19)",
        pattern=(regex(_TO_NINETEEN_RE),),
        prod=_prod_to_nineteen,
    ),
    Rule(
        name="integer (20..90)",
        pattern=(regex(_TENS_RE),),
        prod=_prod_tens,
    ),
    Rule(
        name="powers of tens",
        pattern=(regex(_POWERS_OF_TEN_RE),),
        prod=_prod_powers_of_ten,
    ),
    Rule(
        name="integer 21..99",
        pattern=(
            predicate(_is_tens_20_90, "tens 20..90"),
            predicate(_is_units_1_9, "units 1..9"),
        ),
        prod=_prod_composite_tens,
    ),
    Rule(
        name="integer 21..99 (dashed)",
        pattern=(
            predicate(_is_tens_20_90, "tens 20..90"),
            regex(r"-"),
            predicate(_is_units_1_9, "units 1..9"),
        ),
        prod=_prod_composite_tens,
    ),
    Rule(
        name="one eleven",
        pattern=(regex(_ONE_NINE_RE), regex(_TEN_NINETY_RE)),
        prod=_prod_skip_hundreds_1,
    ),
    Rule(
        name="one twenty two",
        pattern=(regex(_ONE_NINE_RE), regex(_TENS_RE), regex(_ONE_NINE_RE)),
        prod=_prod_skip_hundreds_2,
    ),
    Rule(
        name="one point 2",
        pattern=(
            predicate(is_numeral, "is_numeral"),
            regex(r"point|dot"),
            predicate(_no_grain, "no grain"),
        ),
        prod=_prod_dot_spelled_out,
    ),
    Rule(
        name="point 77",
        pattern=(
            regex(r"point|dot"),
            predicate(_no_grain, "no grain"),
        ),
        prod=_prod_leading_dot_spelled_out,
    ),
    Rule(
        name="decimal number",
        pattern=(regex(r"(\d*\.\d+)"),),
        prod=_prod_decimals,
    ),
    Rule(
        name="comma-separated numbers",
        pattern=(regex(r"(\d+(,\d\d\d)+(\.\d+)?)"),),
        prod=_prod_commas,
    ),
    Rule(
        name="suffixes (K,M,G)",
        pattern=(
            predicate(is_numeral, "is_numeral"),
            regex(r"(k|m|g)(?=[\W$€¢£]|$)"),
        ),
        prod=_prod_suffixes,
    ),
    Rule(
        name="negative numbers",
        pattern=(
            regex(r"(-|minus|negative)(?!\s*-)"),
            predicate(is_positive, "is_positive"),
        ),
        prod=_prod_negative,
    ),
    Rule(
        name="intersect 2 numbers",
        pattern=(
            predicate(_has_grain_positive, "hasGrain & isPositive"),
            predicate(_not_multipliable_positive, "!isMultipliable & isPositive"),
        ),
        prod=_prod_sum,
    ),
    Rule(
        name="intersect 2 numbers (with and)",
        pattern=(
            predicate(_has_grain_positive, "hasGrain & isPositive"),
            regex(r"and"),
            predicate(_not_multipliable_positive, "!isMultipliable & isPositive"),
        ),
        prod=_prod_sum,
    ),
    Rule(
        name="compose by multiplication",
        pattern=(
            predicate(_is_positive_or_zero, "is_positive_or_zero"),
            predicate(is_multipliable, "is_multipliable"),
        ),
        prod=_prod_multiply,
    ),
    Rule(
        name="a dozen of",
        pattern=(regex(r"\b(a )?dozens?( of)?\b"),),
        prod=_prod_dozen,
    ),
    Rule(
        name="<integer> '('<integer>')'",
        pattern=(
            predicate(_is_integer_positive, "positive integer"),
            regex(r"\("),
            predicate(_is_integer_positive, "positive integer"),
            regex(r"\)"),
        ),
        prod=_prod_legal_parens,
    ),
)
