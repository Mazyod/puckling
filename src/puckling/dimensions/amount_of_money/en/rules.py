"""AmountOfMoney/EN/Rules.hs — Python port.

Mirrors Duckling's English money rules: currency tokens (symbols/codes/names),
amount + currency composition in either order, and ``<amount> and <cents>``
intersect rules. The numeric-handling rule produces a transient ``numeral``
token from ``\\d+(\\.\\d+)?`` so this dimension stands on its own when no
Numeral rules are loaded yet.

Upstream:
    https://raw.githubusercontent.com/facebook/duckling/main/Duckling/AmountOfMoney/EN/Rules.hs
    https://raw.githubusercontent.com/facebook/duckling/main/Duckling/AmountOfMoney/Rules.hs
"""

from __future__ import annotations

import re

from puckling.dimensions.amount_of_money.types import AmountOfMoneyValue, money
from puckling.dimensions.numeral.types import NumeralValue
from puckling.predicates import is_natural, is_numeral
from puckling.types import Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Currency mapping (subset of Duckling's table — the locales puckling targets
# plus the codes/symbols English speakers most often write).
# ---------------------------------------------------------------------------

_CURRENCY_BY_TOKEN: dict[str, str] = {
    # ISO codes
    "aed": "AED",
    "aud": "AUD",
    "bgn": "BGN",
    "brl": "BRL",
    "cad": "CAD",
    "chf": "CHF",
    "cny": "CNY",
    "czk": "CZK",
    "dkk": "DKK",
    "egp": "EGP",
    "eur": "EUR",
    "gbp": "GBP",
    "hkd": "HKD",
    "ils": "ILS",
    "inr": "INR",
    "jpy": "JPY",
    "kwd": "KWD",
    "lbp": "LBP",
    "mad": "MAD",
    "mnt": "MNT",
    "myr": "MYR",
    "nok": "NOK",
    "nzd": "NZD",
    "pkr": "PKR",
    "pln": "PLN",
    "qar": "QAR",
    "ron": "RON",
    "rub": "RUB",
    "sar": "SAR",
    "sek": "SEK",
    "sgd": "SGD",
    "thb": "THB",
    "try": "TRY",
    "uah": "UAH",
    "usd": "USD",
    "vnd": "VND",
    "zar": "ZAR",
    # Symbols — for the EN locale "$" defaults to USD.
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "¢": "cent",
    "₪": "ILS",
    "₽": "RUB",
    "₴": "UAH",
    "₮": "MNT",
    "₺": "TRY",
    # English currency words (singular & plural). The spec maps bare "dollar"
    # to USD for EN; ambiguous origin is resolved by locale here.
    "dollar": "USD",
    "dollars": "USD",
    "euro": "EUR",
    "euros": "EUR",
    "pound": "GBP",
    "pounds": "GBP",
    "yen": "JPY",
    "yuan": "CNY",
    "rupee": "INR",
    "rupees": "INR",
    "rs": "INR",
    "rs.": "INR",
    "dinar": "dinar",
    "dinars": "dinar",
    "rial": "rial",
    "rials": "rial",
    "riyal": "riyal",
    "riyals": "riyal",
    "tugrik": "MNT",
    "tugriks": "MNT",
    # Composite codes
    "us$": "USD",
}


def _currency_pattern() -> str:
    # Order longest-first so e.g. "us$" beats "$" and "rs." beats "rs".
    keys = sorted(_CURRENCY_BY_TOKEN, key=len, reverse=True)
    alpha = [re.escape(k) for k in keys if any(ch.isascii() and ch.isalpha() for ch in k)]
    symbols = [re.escape(k) for k in keys if not any(ch.isascii() and ch.isalpha() for ch in k)]
    parts = []
    if alpha:
        parts.append(r"(?<![A-Za-z])(" + "|".join(alpha) + r")(?![A-Za-z])")
    if symbols:
        parts.append("(" + "|".join(symbols) + ")")
    return "|".join(parts)


# ---------------------------------------------------------------------------
# Predicates
# ---------------------------------------------------------------------------


def _is_currency_only(t: Token) -> bool:
    return (
        t.dim == "amount_of_money"
        and isinstance(t.value, AmountOfMoneyValue)
        and t.value.currency is not None
        and t.value.value is None
    )


def _is_simple_money(t: Token) -> bool:
    return (
        t.dim == "amount_of_money"
        and isinstance(t.value, AmountOfMoneyValue)
        and t.value.value is not None
        and t.value.currency is not None
    )


def _is_without_cents(t: Token) -> bool:
    # Whole-number amounts are eligible to absorb a trailing cents component.
    if not _is_simple_money(t):
        return False
    v = t.value.value
    return isinstance(v, (int, float)) and float(v).is_integer()


def _is_cent_money(t: Token) -> bool:
    return (
        t.dim == "amount_of_money"
        and isinstance(t.value, AmountOfMoneyValue)
        and t.value.currency == "cent"
        and t.value.value is not None
    )


# ---------------------------------------------------------------------------
# Productions
# ---------------------------------------------------------------------------


def _prod_number(tokens: tuple[Token, ...]) -> Token | None:
    text = tokens[0].value.text
    try:
        v: int | float = int(text)
    except ValueError:
        v = float(text)
    return Token(dim="numeral", value=NumeralValue(value=v))


def _prod_currency(tokens: tuple[Token, ...]) -> Token | None:
    raw = tokens[0].value.text.lower()
    code = _CURRENCY_BY_TOKEN.get(raw)
    if code is None:
        return None
    return Token(dim="amount_of_money", value=money(value=None, currency=code))


def _prod_cent_word(tokens: tuple[Token, ...]) -> Token | None:
    return Token(dim="amount_of_money", value=money(value=None, currency="cent"))


def _prod_amount_unit(tokens: tuple[Token, ...]) -> Token | None:
    # <amount> <currency>
    n = tokens[0].value.value
    c = tokens[1].value.currency
    if n is None or c is None:
        return None
    return Token(dim="amount_of_money", value=money(value=n, currency=c))


def _prod_unit_amount(tokens: tuple[Token, ...]) -> Token | None:
    # <currency> <amount>
    c = tokens[0].value.currency
    n = tokens[1].value.value
    if n is None or c is None:
        return None
    return Token(dim="amount_of_money", value=money(value=n, currency=c))


def _with_cents(amount: AmountOfMoneyValue, cents: float) -> AmountOfMoneyValue:
    base = 0.0 if amount.value is None else float(amount.value)
    return AmountOfMoneyValue(value=base + float(cents) / 100.0, currency=amount.currency)


def _intersect_at(idx: int):
    """Build a production that combines tokens[0] (money) with tokens[idx]'s value as cents."""

    def prod(tokens: tuple[Token, ...]) -> Token | None:
        cents = tokens[idx].value.value
        if cents is None:
            return None
        return Token(dim="amount_of_money", value=_with_cents(tokens[0].value, cents))

    return prod


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------


RULES: tuple[Rule, ...] = (
    # Numeric-handling rule (mandated by spec): integers and decimals.
    Rule(
        name="integer (numeric)",
        pattern=(regex(r"\d+(\.\d+)?"),),
        prod=_prod_number,
    ),
    # Cent words and the "c" abbreviation — produce a cent currency token.
    Rule(
        name="cent",
        pattern=(regex(r"\b(?:cents?|penn(?:y|ies)|pence|sens?)\b|(?<![A-Za-z])c\b"),),
        prod=_prod_cent_word,
    ),
    # All other currencies — symbols, codes, words.
    Rule(
        name="currencies",
        pattern=(regex(_currency_pattern()),),
        prod=_prod_currency,
    ),
    # <amount> <currency>  e.g. "50 dollars", "20€"
    Rule(
        name="<amount> <currency>",
        pattern=(
            predicate(is_numeral, "is_numeral"),
            predicate(_is_currency_only, "is_currency_only"),
        ),
        prod=_prod_amount_unit,
    ),
    # <currency> <amount>  e.g. "$50", "USD 50"
    Rule(
        name="<currency> <amount>",
        pattern=(
            predicate(_is_currency_only, "is_currency_only"),
            predicate(is_numeral, "is_numeral"),
        ),
        prod=_prod_unit_amount,
    ),
    # <amount> <X cents>  e.g. "$20 43c"
    # TODO(puckling): edge case — only fires when both sides parse as money.
    Rule(
        name="intersect (X cents)",
        pattern=(
            predicate(_is_without_cents, "is_without_cents"),
            predicate(_is_cent_money, "is_cent_money"),
        ),
        prod=_intersect_at(1),
    ),
    # <amount> "and" <X cents>  e.g. "$20 and 43c"
    Rule(
        name="intersect (and X cents)",
        pattern=(
            predicate(_is_without_cents, "is_without_cents"),
            regex(r"and"),
            predicate(_is_cent_money, "is_cent_money"),
        ),
        prod=_intersect_at(2),
    ),
    # <amount> <natural>  e.g. "$20 43"
    # TODO(puckling): edge case — accepts trailing bare numerals as cents.
    Rule(
        name="intersect",
        pattern=(
            predicate(_is_without_cents, "is_without_cents"),
            predicate(is_natural, "is_natural"),
        ),
        prod=_intersect_at(1),
    ),
    # <amount> "and" <natural>  e.g. "$20 and 43"
    Rule(
        name="intersect (and number)",
        pattern=(
            predicate(_is_without_cents, "is_without_cents"),
            regex(r"and"),
            predicate(is_natural, "is_natural"),
        ),
        prod=_intersect_at(2),
    ),
)
