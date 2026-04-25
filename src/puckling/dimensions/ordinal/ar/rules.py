"""Arabic ordinal rules — ported from Duckling/Ordinal/AR/Rules.hs."""

from __future__ import annotations

from puckling.dimensions.ordinal.types import ordinal
from puckling.types import RegexMatch, Rule, Token, regex

# Maps the Arabic ordinal stems for 1..10 to their integer values.
_ORDINALS_MAP: dict[str, int] = {
    "اول": 1,
    "أول": 1,
    "حاد": 1,
    "حادي": 1,
    "واحد": 1,
    "ثان": 2,
    "ثاني": 2,
    "ثالث": 3,
    "رابع": 4,
    "خامس": 5,
    "سادس": 6,
    "سابع": 7,
    "ثامن": 8,
    "تاسع": 9,
    "عاشر": 10,
}

# Maps the Arabic cardinal stems for 20..90 to their integer values.
# The "ون"/"ين" suffix is captured separately and dropped (masculine vs.
# feminine forms collapse to the same value).
_CARDINALS_MAP: dict[str, int] = {
    "عشر": 20,
    "ثلاث": 30,
    "اربع": 40,
    "خمس": 50,
    "ست": 60,
    "سبع": 70,
    "ثمان": 80,
    "تسع": 90,
}


def _captured(tokens: tuple[Token, ...], index: int) -> str | None:
    """Return the `index`-th capture group of the leading regex token, or None."""
    if not tokens:
        return None
    head = tokens[0]
    if not isinstance(head.value, RegexMatch):
        return None
    groups = head.value.groups
    if index >= len(groups):
        return None
    g = groups[index]
    return g.lower() if g is not None else None


def _lookup_ordinal(
    tokens: tuple[Token, ...],
    table: dict[str, int],
    *,
    offset: int = 0,
    index: int = 0,
) -> Token | None:
    """Resolve an ordinal by looking the captured stem up in `table` and adding `offset`."""
    stem = _captured(tokens, index)
    if stem is None:
        return None
    value = table.get(stem)
    if value is None:
        return None
    return Token(dim="ordinal", value=ordinal(offset + value))


def _composite_ordinals(tokens: tuple[Token, ...]) -> Token | None:
    units_stem = _captured(tokens, 0)
    tens_stem = _captured(tokens, 1)
    if units_stem is None or tens_stem is None:
        return None
    units = _ORDINALS_MAP.get(units_stem)
    tens = _CARDINALS_MAP.get(tens_stem)
    if units is None or tens is None:
        return None
    return Token(dim="ordinal", value=ordinal(units + tens))


def _ordinals_1_to_10(tokens: tuple[Token, ...]) -> Token | None:
    return _lookup_ordinal(tokens, _ORDINALS_MAP)


def _ordinals_11(_tokens: tuple[Token, ...]) -> Token | None:
    return Token(dim="ordinal", value=ordinal(11))


def _ordinals_12(_tokens: tuple[Token, ...]) -> Token | None:
    return Token(dim="ordinal", value=ordinal(12))


def _ordinals_13_to_19(tokens: tuple[Token, ...]) -> Token | None:
    return _lookup_ordinal(tokens, _ORDINALS_MAP, offset=10)


def _ordinals_tens(tokens: tuple[Token, ...]) -> Token | None:
    return _lookup_ordinal(tokens, _CARDINALS_MAP)


RULES: tuple[Rule, ...] = (
    Rule(
        name="ordinals (composite, e.g., eighty-seven)",
        pattern=(
            regex(
                r"ال(واحد|حادي?|ثاني?|ثالث|رابع|خامس|سادس|سابع|ثامن|تاسع|عاشر)"
                r" و ?ال(عشر|ثلاث|اربع|خمس|ست|سبع|ثمان|تسع)(ون|ين)"
            ),
        ),
        prod=_composite_ordinals,
    ),
    Rule(
        name="ordinals (first..tenth)",
        pattern=(
            regex(r"(?:ال)?([أا]ول|ثاني?|ثالث|رابع|خامس|سادس|سابع|ثامن|تاسع|عاشر)[ةهى]?"),
        ),
        prod=_ordinals_1_to_10,
    ),
    Rule(
        name="ordinals (eleventh)",
        pattern=(regex(r"ال([اأإ]حد[يى]?|حاد(?:ي[ةه]?)?) ?عشر[ةه]?"),),
        prod=_ordinals_11,
    ),
    Rule(
        name="ordinals (twelveth)",
        pattern=(regex(r"ال([اأإ]ثن[يى]?|ثان(?:ي[ةه]?)?) ?عشر[ةه]?"),),
        prod=_ordinals_12,
    ),
    Rule(
        name="ordinals (thirtieth..nineteenth)",
        pattern=(regex(r"ال(ثالث|رابع|خامس|سادس|سابع|ثامن|تاسع)[ةه]? ?عشرة?"),),
        prod=_ordinals_13_to_19,
    ),
    Rule(
        name="ordinals (twenty, thirty..ninety)",
        pattern=(regex(r"ال(عشر|ثلاث|اربع|خمس|ست|سبع|ثمان|تسع)(ون|ين)"),),
        prod=_ordinals_tens,
    ),
)
