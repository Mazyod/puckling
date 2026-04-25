"""Arabic locale rules for the distance dimension.

Upstream Duckling does not ship a `Duckling/Distance/AR` package; this module
adapts the imperial/metric distance rules from `Duckling/Distance/EN/Rules.hs`
into Arabic, modelled on the Arabic patterns used in `Duckling/Volume/AR`.

Each rule pairs a numeral token with a unit regex. A small digit-seeding rule
handles bare Arabic-Indic and ASCII digit runs, so phrases like "٥ كم" parse
even when no other numeral rule has fired.
"""

from __future__ import annotations

from puckling.dimensions.distance.types import DistanceUnit, DistanceValue
from puckling.dimensions.numeral.helpers import parse_arabic_int
from puckling.dimensions.numeral.types import NumeralValue
from puckling.predicates import is_numeral
from puckling.types import RegexMatch, Rule, Token, predicate, regex

# Numeral seed so phrases like "٥ كم" parse without depending on the full
# AR Numeral grammar — mirrors `ruleInteger (numeric)` in upstream Duckling.
_DIGITS_RE = r"[٠-٩]+|[0-9]+"


def _prod_digits(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[0].value
    if not isinstance(m, RegexMatch):
        return None
    return Token(dim="numeral", value=NumeralValue(value=parse_arabic_int(m.text)))


def _make_distance_prod(unit: DistanceUnit):
    def prod(tokens: tuple[Token, ...]) -> Token | None:
        n = tokens[0].value.value
        return Token(dim="distance", value=DistanceValue(value=n, unit=unit))

    return prod


_NUMERAL = predicate(is_numeral, "is_numeral")


def _distance_rule(name: str, unit: DistanceUnit, unit_re: str) -> Rule:
    return Rule(
        name=name,
        pattern=(_NUMERAL, regex(unit_re)),
        prod=_make_distance_prod(unit),
    )


# Arabic spellings tolerate common variants (singular / plural / abbreviation):
#   كيلومتر / كيلو متر / كم
#   متر / أمتار
#   سنتيمتر / سم
#   ميليمتر / مم
#   ميل / أميال
#   ياردة / ياردات
#   قدم / أقدام
#   بوصة / بوصات / إنش
# TODO(puckling): edge case — Arabic dual forms (e.g. "كيلومتران", "ميلان")
# would require a dedicated rule; we expect digit-led forms in v1.

RULES: tuple[Rule, ...] = (
    Rule(
        name="integer (numeric, AR digits)",
        pattern=(regex(_DIGITS_RE),),
        prod=_prod_digits,
    ),
    _distance_rule("<n> كيلومتر", DistanceUnit.KILOMETRE, r"كيلو ?متر(ات)?|كم"),
    _distance_rule("<n> سنتيمتر", DistanceUnit.CENTIMETRE, r"سنتي? ?متر(ات)?|سم"),
    _distance_rule("<n> ميليمتر", DistanceUnit.MILLIMETRE, r"مي?لي? ?متر(ات)?|مم"),
    _distance_rule("<n> متر", DistanceUnit.METRE, r"أمتار|متر(ات)?|م\b"),
    _distance_rule("<n> ميل", DistanceUnit.MILE, r"أميال|ميل|ميول"),
    _distance_rule("<n> ياردة", DistanceUnit.YARD, r"ياردات|يارد[ةه]?"),
    _distance_rule("<n> قدم", DistanceUnit.FOOT, r"أقدام|قدم"),
    _distance_rule("<n> بوصة", DistanceUnit.INCH, r"بوصات|بوص[ةه]?|إنش|انش"),
)
