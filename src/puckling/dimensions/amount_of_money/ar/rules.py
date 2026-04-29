"""Arabic AmountOfMoney rules.

Ported (minimally) from Duckling's `Duckling/AmountOfMoney/AR/Rules.hs`. Covers
the most common Gulf and Levantine currencies along with a handful of generic
forms (دينار, ريال, درهم, جنيه, دولار, يورو) and their ISO codes.

This module also seeds a thin "digits-only" numeral rule so unit-name rules can
match a preceding number via predicate. Word-form numerals are the Numeral
dimension's responsibility.
"""

from __future__ import annotations

from puckling.dimensions.amount_of_money.types import money
from puckling.dimensions.numeral.helpers import parse_arabic_decimal
from puckling.dimensions.numeral.types import NumeralValue
from puckling.predicates import is_numeral, is_positive
from puckling.types import Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Numeral seed (digits only).
#
# Accepts ASCII digits ("42", "3.14") or Arabic-Indic digits ("٤٢", "٣٫١٤").
# Regexes run overlapped, so guards prevent matching inside attached words or
# punctuation-fragmented numbers like "10,5 دولار".

_AR_WORD_BOUND_R = r"(?![\p{L}\p{N}])"
_NUMERIC_RE = r"(?<![\p{L}\p{N}.,٫])(?:[٠-٩]+(?:٫[٠-٩]+)?|\d+(?:\.\d+)?)"


def _word_currency(pattern: str) -> str:
    return rf"(?:{pattern}){_AR_WORD_BOUND_R}"


def _prod_numeral(tokens: tuple[Token, ...]) -> Token:
    text = tokens[0].value.text
    return Token(dim="numeral", value=NumeralValue(value=parse_arabic_decimal(text)))


# ---------------------------------------------------------------------------
# Production helpers.


def _make_amount_prod(currency: str):
    def go(tokens: tuple[Token, ...]) -> Token:
        n = tokens[0].value.value
        return Token(
            dim="amount_of_money",
            value=money(value=n, currency=currency),
        )

    return go


def _make_amount_prod_right(currency: str):
    """Same as `_make_amount_prod`, but the numeral is the second matched token."""

    def go(tokens: tuple[Token, ...]) -> Token:
        n = tokens[1].value.value
        return Token(
            dim="amount_of_money",
            value=money(value=n, currency=currency),
        )

    return go


_prod_kwd = _make_amount_prod("KWD")
_prod_sar = _make_amount_prod("SAR")
_prod_aed = _make_amount_prod("AED")
_prod_qar = _make_amount_prod("QAR")
_prod_jod = _make_amount_prod("JOD")
_prod_iqd = _make_amount_prod("IQD")
_prod_egp = _make_amount_prod("EGP")
_prod_gbp = _make_amount_prod("GBP")
_prod_lbp = _make_amount_prod("LBP")
_prod_mad = _make_amount_prod("MAD")
_prod_usd = _make_amount_prod("USD")
_prod_eur = _make_amount_prod("EUR")
_prod_ils = _make_amount_prod("ILS")
_prod_dinar = _make_amount_prod("Dinar")
_prod_dirham = _make_amount_prod("Dirham")
_prod_riyal = _make_amount_prod("Riyal")
_prod_pound = _make_amount_prod("Pound")


_NUM = predicate(is_positive, "is_positive")
_ANY_NUM = predicate(is_numeral, "is_numeral")


_ISO_CODES: tuple[str, ...] = ("KWD", "SAR", "AED", "QAR", "JOD", "EGP", "LBP", "USD")


def _prod_iso(tokens: tuple[Token, ...]) -> Token:
    n = tokens[0].value.value
    code = tokens[1].value.text.upper()
    return Token(dim="amount_of_money", value=money(value=n, currency=code))


RULES: tuple[Rule, ...] = (
    Rule(
        name="integer (numeric, ar/en digits)",
        pattern=(regex(_NUMERIC_RE),),
        prod=_prod_numeral,
    ),
    # ---- Country-qualified currencies (must match before generic words). ----
    Rule(
        name="<n> دينار كويتي → KWD",
        pattern=(_NUM, regex(_word_currency(r"(?:دينار|دنانير)\s+كويتي[ةه]?|د\.ك"))),
        prod=_prod_kwd,
    ),
    Rule(
        name="<n> دينار أردني → JOD",
        pattern=(_NUM, regex(_word_currency(r"(?:دينار|دنانير)\s+[أا]ردني[ةه]?"))),
        prod=_prod_jod,
    ),
    Rule(
        name="<n> دينار عراقي → IQD",
        pattern=(_NUM, regex(_word_currency(r"(?:دينار|دنانير)\s+عراقي[ةه]?"))),
        prod=_prod_iqd,
    ),
    Rule(
        name="<n> ريال سعودي → SAR",
        pattern=(_NUM, regex(_word_currency(r"(?:ريال|ريالات)\s+سعودي[ةه]?"))),
        prod=_prod_sar,
    ),
    Rule(
        name="<n> ريال قطري → QAR",
        pattern=(_NUM, regex(_word_currency(r"(?:ريال|ريالات)\s+قطري[ةه]?"))),
        prod=_prod_qar,
    ),
    Rule(
        name="<n> درهم إماراتي → AED",
        pattern=(_NUM, regex(_word_currency(r"(?:درهم|دراهم)\s+[إا]ماراتي[ةه]?"))),
        prod=_prod_aed,
    ),
    Rule(
        name="<n> درهم مغربي → MAD",
        pattern=(_NUM, regex(_word_currency(r"(?:درهم|دراهم)\s+مغربي[ةه]?"))),
        prod=_prod_mad,
    ),
    Rule(
        name="<n> جنيه مصري → EGP",
        pattern=(_NUM, regex(_word_currency(r"جنيه(?:ات)?\s+مصري[ةه]?|ج\.م\.?"))),
        prod=_prod_egp,
    ),
    Rule(
        name="<n> جنيه استرليني → GBP",
        pattern=(_NUM, regex(_word_currency(r"جنيه(?:ات)?\s+استرليني[ةه]?"))),
        prod=_prod_gbp,
    ),
    Rule(
        name="<n> ليرة لبنانية → LBP",
        pattern=(_NUM, regex(_word_currency(r"لير(?:ة|ه|ات)\s+لبناني[ةه]?"))),
        prod=_prod_lbp,
    ),
    # ---- Generic single-word currencies (lower priority via later position). ----
    Rule(
        name="<n> دينار → Dinar",
        pattern=(_NUM, regex(_word_currency(r"دينار|دنانير"))),
        prod=_prod_dinar,
    ),
    Rule(
        name="<n> ريال → Riyal",
        pattern=(_NUM, regex(_word_currency(r"ريال(?:ات)?"))),
        prod=_prod_riyal,
    ),
    Rule(
        name="<n> درهم → Dirham",
        pattern=(_NUM, regex(_word_currency(r"درا?هم"))),
        prod=_prod_dirham,
    ),
    Rule(
        name="<n> جنيه → Pound",
        pattern=(_NUM, regex(_word_currency(r"جنيه(?:ات)?"))),
        prod=_prod_pound,
    ),
    Rule(
        name="<n> دولار → USD",
        pattern=(_NUM, regex(_word_currency(r"دولار(?:ات)?"))),
        prod=_prod_usd,
    ),
    Rule(
        name="<n> يورو → EUR",
        pattern=(_NUM, regex(_word_currency(r"[أاي]ورو|€"))),
        prod=_prod_eur,
    ),
    Rule(
        name="<n> شيكل → ILS",
        # TODO(puckling): edge case — also accepts شواقل/شيقل with q/k variants.
        pattern=(_NUM, regex(_word_currency(r"شي?[كق]ل|شوا[كق]ل"))),
        prod=_prod_ils,
    ),
    # ---- ISO codes (collapsed: regex captures the code, prod resolves it). ----
    Rule(
        name="<n> <ISO>",
        pattern=(_ANY_NUM, regex(rf"(?:{'|'.join(_ISO_CODES)})\b")),
        prod=_prod_iso,
    ),
    # $ adjacent to a number → USD.
    Rule(
        name="$ <n> → USD",
        pattern=(regex(r"\$"), _ANY_NUM),
        prod=_make_amount_prod_right("USD"),
    ),
    Rule(
        name="<n> $ → USD",
        pattern=(_ANY_NUM, regex(r"\$")),
        prod=_make_amount_prod("USD"),
    ),
)
