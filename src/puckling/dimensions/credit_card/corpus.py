"""Corpus for the locale-agnostic ``credit_card`` dimension.

Mirrors ``Duckling/CreditCardNumber/Corpus.hs``: positive examples paired with
expected resolved values.
"""

from __future__ import annotations

from puckling.corpus import Example, examples


def _value(number: str, issuer: str) -> dict:
    """Build the resolved-value dict that ``CreditCardValue.resolve`` emits."""
    return {"value": number, "issuer": issuer, "type": "value"}


CORPUS: tuple[Example, ...] = (
    examples(
        _value("4111111111111111", "visa"),
        ["4111111111111111", "4111-1111-1111-1111"],
    ),
    examples(
        _value("371449635398431", "amex"),
        ["371449635398431", "3714-496353-98431"],
    ),
    examples(
        _value("6011111111111117", "discover"),
        ["6011111111111117", "6011-1111-1111-1117"],
    ),
    examples(
        _value("5555555555554444", "mastercard"),
        ["5555555555554444", "5555-5555-5555-4444"],
    ),
    examples(
        _value("30569309025904", "diner club"),
        ["30569309025904", "3056-930902-5904"],
    ),
    examples(
        _value("3530111333300000", "other"),
        ["3530111333300000"],
    ),
)


# Negative examples — strings that must not parse as credit cards. Mirrors
# upstream ``negativeCorpus``. Surfaced so tests can exercise rejection.
NEGATIVE_CORPUS: tuple[str, ...] = (
    "0" * 7,  # below minNumberDigits
    "0" * 20,  # above maxNumberDigits
    "invalid",
    "4111111111111110",  # bad Luhn (Visa)
    "41111111-1111-1111",  # malformed grouping
    "371449635398430",  # bad Luhn (Amex)
    "3714496353-98431",  # malformed grouping
    "6011111111111110",  # bad Luhn (Discover)
    "60111111-1111-1117",  # malformed grouping
    "5555555555554440",  # bad Luhn (Mastercard)
    "55555555-5555-4444",  # malformed grouping
    "30569309025900",  # bad Luhn (Diner Club)
    "3056930902-5904",  # malformed grouping
)


__all__ = ["CORPUS", "NEGATIVE_CORPUS"]
