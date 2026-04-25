"""English ordinal rules.

Translated faithfully from Duckling's ``Duckling/Ordinal/EN/Rules.hs``:
three rules cover simple ordinals ("first" .. "ninetieth"), composite
ordinals ("twenty-fifth", "thirtyfirst"), and digit ordinals ("1st", "25th").
"""

from __future__ import annotations

from puckling.dimensions.ordinal.types import ordinal
from puckling.types import RegexMatch, Rule, Token, regex

# Word -> int maps mirroring `ordinalsMap` and `cardinalsMap` in the Haskell source.
ORDINALS_MAP: dict[str, int] = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
    "eleventh": 11,
    "twelfth": 12,
    "thirteenth": 13,
    "fourteenth": 14,
    "fifteenth": 15,
    "sixteenth": 16,
    "seventeenth": 17,
    "eighteenth": 18,
    "nineteenth": 19,
    "twentieth": 20,
    "thirtieth": 30,
    "fortieth": 40,
    "fiftieth": 50,
    "sixtieth": 60,
    "seventieth": 70,
    "eightieth": 80,
    "ninetieth": 90,
}

CARDINALS_MAP: dict[str, int] = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

_ORDINAL_WORDS = "|".join(ORDINALS_MAP)
_TENS_WORDS = "|".join(CARDINALS_MAP)
_UNIT_WORDS = "first|second|third|fourth|fifth|sixth|seventh|eighth|ninth"


def _ordinal_token(value: int) -> Token:
    return Token(dim="ordinal", value=ordinal(value))


def _prod_ordinal_words(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value
    if not isinstance(match, RegexMatch):
        return None
    word = (match.groups[0] or "").lower()
    n = ORDINALS_MAP.get(word)
    if n is None:
        return None
    return _ordinal_token(n)


def _prod_composite_ordinal(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value
    if not isinstance(match, RegexMatch):
        return None
    tens = (match.groups[0] or "").lower()
    units = (match.groups[1] or "").lower()
    tt = CARDINALS_MAP.get(tens)
    uu = ORDINALS_MAP.get(units)
    if tt is None or uu is None:
        return None
    return _ordinal_token(tt + uu)


def _prod_ordinal_digits(tokens: tuple[Token, ...]) -> Token | None:
    match = tokens[0].value
    if not isinstance(match, RegexMatch):
        return None
    digits = match.groups[0]
    if not digits:
        return None
    try:
        n = int(digits)
    except ValueError:
        return None
    return _ordinal_token(n)


RULES: tuple[Rule, ...] = (
    Rule(
        name="ordinals (first..twentieth,thirtieth,...)",
        pattern=(regex(rf"({_ORDINAL_WORDS})"),),
        prod=_prod_ordinal_words,
    ),
    Rule(
        name="ordinals (composite, e.g. eighty-seven, forty—seventh, twenty ninth, thirtythird)",
        pattern=(regex(rf"({_TENS_WORDS})[\s\-—]?({_UNIT_WORDS})"),),
        prod=_prod_composite_ordinal,
    ),
    Rule(
        name="ordinal (digits)",
        pattern=(regex(r"0*(\d+) ?(st|nd|rd|th)"),),
        prod=_prod_ordinal_digits,
    ),
)
