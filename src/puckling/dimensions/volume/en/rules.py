"""English Volume rules — port of `Duckling/Volume/EN/Rules.hs`.

The upstream Haskell module relies on a numeral parser supplying values; in the
current puckling foundation no English numeral rule pack exists yet, so this
module ships the small set of numeric tokens (digits, decimals, simple fractions
and a handful of word numerals) needed by the EN volume corpus. Once a real
numeral rule pack lands these helpers should be removed in favour of the
shared `is_numeral` predicate.

Interval rules (`between`, `under`, `over`) and the standalone "unit-only"
latent rules from upstream are intentionally omitted — the puckling
`VolumeValue` dataclass cannot yet express min/max/interval shapes.
"""

from __future__ import annotations

from puckling.dimensions.numeral.types import NumeralValue
from puckling.dimensions.volume.types import VolumeUnit, VolumeValue
from puckling.predicates import is_dim, is_numeral
from puckling.types import Rule, Token, predicate, regex

_BOUNDARY_L = r"(?<![\p{L}\p{N}_])"
_BOUNDARY_R = r"(?!\s*/)(?![\p{L}\p{N}_])"
_NUMERIC_RE = r"(?<![\p{L}\p{N}_./-])\d+(\.\d+)?"
_NUMERIC_CONTEXT_RE = r"\d+(?:\.\d+)?"
_UNSUPPORTED_VOLUME_SHAPE_GUARD = (
    rf"(?<!\b{_NUMERIC_CONTEXT_RE}\s*[-–—]\s*{_NUMERIC_CONTEXT_RE}\s*)"
    rf"(?<!\b{_NUMERIC_CONTEXT_RE}\s+to\s+{_NUMERIC_CONTEXT_RE}\s*)"
    rf"(?<!\bfrom\s+{_NUMERIC_CONTEXT_RE}\s*[^\s\d]+\s+to\s+{_NUMERIC_CONTEXT_RE}\s*)"
    rf"(?<!\bbetween\s+{_NUMERIC_CONTEXT_RE}\s+and\s+{_NUMERIC_CONTEXT_RE}\s*)"
    rf"(?<!\b(?:under|below|less\s+than|not\s+more\s+than|no\s+more\s+than|"
    rf"over|above|at\s+least|more\s+than|at\s+most)\s+{_NUMERIC_CONTEXT_RE}\s*)"
)
_UNSUPPORTED_VOLUME_SHAPE_RIGHT_GUARD = rf"(?!\s*(?:[-–—]|to\b)\s*{_NUMERIC_CONTEXT_RE})"


def _guarded_unit_pattern(pattern_re: str) -> str:
    return (
        f"{_UNSUPPORTED_VOLUME_SHAPE_GUARD}"
        f"(?:{pattern_re})"
        f"{_UNSUPPORTED_VOLUME_SHAPE_RIGHT_GUARD}"
        f"{_BOUNDARY_R}"
    )


# ---------------------------------------------------------------------------
# numeral helpers (regex-driven; supplies tokens of dim="numeral")
#
# These exist only because no English numeral rule pack is available yet.
# TODO(puckling): edge case — drop once `numeral/en/rules.py` lands.

_WORD_NUMERALS: dict[str, int] = {
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
    "thousand": 1000,
}


def _prod_digits(tokens: tuple[Token, ...]) -> Token | None:
    text = tokens[0].value.text
    value: int | float = float(text) if "." in text else int(text)
    return Token(dim="numeral", value=NumeralValue(value=value))


def _prod_word_numeral(tokens: tuple[Token, ...]) -> Token | None:
    word = tokens[0].value.text.lower()
    val = _WORD_NUMERALS.get(word)
    if val is None:
        return None
    return Token(dim="numeral", value=NumeralValue(value=val))


def _prod_simple_fraction(tokens: tuple[Token, ...]) -> Token | None:
    num_str, den_str = tokens[0].value.groups[:2]
    den = int(den_str or 0)
    if den == 0:
        return None
    return Token(dim="numeral", value=NumeralValue(value=int(num_str or 0) / den))


def _prod_indefinite_article(_tokens: tuple[Token, ...]) -> Token | None:
    return Token(dim="numeral", value=NumeralValue(value=1))


_NUMERAL_RULES: tuple[Rule, ...] = (
    Rule(
        name="integer (digits)",
        pattern=(regex(_NUMERIC_RE),),
        prod=_prod_digits,
    ),
    Rule(
        name="word numeral",
        pattern=(
            regex(
                rf"{_BOUNDARY_L}"
                r"(one|two|three|four|five|six|seven|eight|nine|ten|thousand)"
                rf"{_BOUNDARY_R}"
            ),
        ),
        prod=_prod_word_numeral,
    ),
    Rule(
        name="simple fraction",
        pattern=(regex(rf"{_BOUNDARY_L}(\d+)/(\d+)"),),
        prod=_prod_simple_fraction,
    ),
    Rule(
        name="indefinite article (a/an)",
        pattern=(regex(rf"{_BOUNDARY_L}an?{_BOUNDARY_R}"),),
        prod=_prod_indefinite_article,
    ),
)


# ---------------------------------------------------------------------------
# volume unit table — same shape as upstream's `volumes` list

_UNIT_TABLE: tuple[tuple[str, str, VolumeUnit], ...] = (
    ("<vol> ml", r"m(l(s?)|illilit(er|re)s?)", VolumeUnit.MILLILITRE),
    ("<vol> hectoliters", r"hectolit(er|re)s?", VolumeUnit.HECTOLITRE),
    ("<vol> liters", r"l(it(er|re)s?)?", VolumeUnit.LITRE),
    ("<vol> gallon", r"gal((l?ons?)|s)?", VolumeUnit.GALLON),
)


def _make_volume_rule(name: str, pat: str, unit: VolumeUnit) -> Rule:
    def prod(tokens: tuple[Token, ...]) -> Token | None:
        n = tokens[0].value.value
        if not isinstance(n, (int, float)):
            return None
        return Token(dim="volume", value=VolumeValue(value=float(n), unit=unit))

    return Rule(
        name=name,
        pattern=(
            predicate(is_numeral, "is_numeral"),
            regex(_guarded_unit_pattern(pat)),
        ),
        prod=prod,
    )


_VOLUME_UNIT_RULES: tuple[Rule, ...] = tuple(
    _make_volume_rule(name, pat, unit) for (name, pat, unit) in _UNIT_TABLE
)


# ---------------------------------------------------------------------------
# fractional-volume rules — e.g. "half a litre", "quarter-litre"

_FRACTIONS: tuple[tuple[str, str, float], ...] = (
    ("half", r"half(-|(( of)?( an?)?))?", 1 / 2),
    ("third", r"third(-|(( of)?( an?)?))?", 1 / 3),
    ("fourth", r"(quarter|fourth)(-|(( of)?( an?)?))?", 1 / 4),
    ("fifth", r"fifth(-|(( of)?( an?)?))?", 1 / 5),
    ("tenth", r"tenth(-|(( of)?( an?)?))?", 1 / 10),
)


def _make_fraction_rule(
    name: str,
    pat: str,
    factor: float,
    unit_name: str,
    unit_pat: str,
    unit: VolumeUnit,
) -> Rule:
    def prod(_tokens: tuple[Token, ...]) -> Token | None:
        return Token(dim="volume", value=VolumeValue(value=factor, unit=unit))

    return Rule(
        name=f"{name} {unit_name}",
        pattern=(
            regex(f"{_BOUNDARY_L}{pat}"),
            regex(_guarded_unit_pattern(unit_pat)),
        ),
        prod=prod,
    )


_FRACTIONAL_VOLUME_RULES: tuple[Rule, ...] = tuple(
    _make_fraction_rule(frac_name, frac_pat, factor, unit_name, unit_pat, unit)
    for (frac_name, frac_pat, factor) in _FRACTIONS
    for (unit_name, unit_pat, unit) in _UNIT_TABLE
)


# ---------------------------------------------------------------------------
# precision passthrough — "around 3 gallons" surfaces the same volume value


def _prod_precision(tokens: tuple[Token, ...]) -> Token | None:
    return tokens[1]


_PRECISION_RULE: Rule = Rule(
    name="about <volume>",
    pattern=(
        regex(r"~|exactly|precisely|about|approx(\.|imately)?|close to|near( to)?|around|almost"),
        predicate(is_dim("volume"), "is_volume"),
    ),
    prod=_prod_precision,
)


# ---------------------------------------------------------------------------
# TODO(puckling): edge case — interval rules (`between`, `from..to`,
# `under`, `over`, `at most`, `more than`) require a richer VolumeValue
# carrying min/max/interval state. Skipping until the type is extended.

RULES: tuple[Rule, ...] = (
    *_NUMERAL_RULES,
    *_VOLUME_UNIT_RULES,
    *_FRACTIONAL_VOLUME_RULES,
    _PRECISION_RULE,
)
