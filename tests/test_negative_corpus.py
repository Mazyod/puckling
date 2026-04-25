"""Negative-corpus tests — phrases that must NOT produce a dimension's entities.

Fills a real gap in upstream Duckling, where most dimensions have no
``negativeCorpus`` list at all (only Email, URL, CreditCard, and PhoneNumber
have one). Each parametrized case asserts that ``parse(phrase, ctx, dims=(dim,))``
returns an empty list, guarding against accidental regex broadening.
"""

from __future__ import annotations

import pytest

from puckling import Context, DimensionName, Options, parse

# Per-dimension lists of ``(phrase, locale_marker)``. We deliberately avoid
# phrases whose substrings happen to be Arabic numeral words (e.g. ``ست`` for
# "six") or English calendar/duration keywords (e.g. ``sun``, ``a h``,
# ``shuhur``) — those would otherwise trigger spurious sub-span matches.
NEGATIVE_BY_DIM: dict[DimensionName, tuple[tuple[str, str], ...]] = {
    "numeral": (
        ("the quick brown fox", "en"),
        ("hello world", "en"),
        ("lorem ipsum dolor", "en"),
        ("foo bar baz", "en"),
        ("!!!??? ...", "en"),
        ("plain prose only", "en"),
        ("xyz pqr lmn", "en"),
        ("مرحبا بالعالم", "ar"),
        ("صباح الخير", "ar"),
        ("سماء زرقاء", "ar"),
    ),
    "ordinal": (
        ("the cat", "en"),
        ("good morning", "en"),
        ("hello world", "en"),
        ("blue sky", "en"),
        ("apple pie", "en"),
        ("foo bar baz", "en"),
        ("!!!??? ...", "en"),
        ("صباح الخير", "ar"),
        ("سماء زرقاء", "ar"),
    ),
    "time": (
        ("lorem ipsum", "en"),
        ("hello world", "en"),
        ("foo bar baz", "en"),
        ("apple pie recipe", "en"),
        ("blue green yellow", "en"),
        ("plain prose only", "en"),
        ("xyz pqr lmn", "en"),
        ("مرحبا بالعالم", "ar"),
        ("صباح الخير", "ar"),
        ("سماء زرقاء", "ar"),
    ),
    "duration": (
        ("hello world", "en"),
        ("very fast", "en"),
        ("quick", "en"),
        ("blue sky", "en"),
        ("foo bar baz", "en"),
        ("plain prose only", "en"),
        ("the cat sat", "en"),
        ("سماء زرقاء", "ar"),
        ("صباح الخير", "ar"),
        ("سريع جدا", "ar"),
    ),
    "distance": (
        ("hello world", "en"),
        ("blue sky", "en"),
        ("apple pie", "en"),
        ("good morning", "en"),
        ("foo bar baz", "en"),
        ("plain prose only", "en"),
        ("سماء زرقاء", "ar"),
        ("صباح الخير", "ar"),
    ),
    "temperature": (
        ("hello world", "en"),
        ("very hot", "en"),
        ("warm weather", "en"),
        ("apple pie", "en"),
        ("foo bar baz", "en"),
        ("plain prose only", "en"),
        ("سماء زرقاء", "ar"),
        ("صباح الخير", "ar"),
        ("جو حار", "ar"),
    ),
    "quantity": (
        ("hello world", "en"),
        ("blue sky", "en"),
        ("apple pie", "en"),
        ("good morning", "en"),
        ("foo bar baz", "en"),
        ("plain prose only", "en"),
        ("سماء زرقاء", "ar"),
        ("صباح الخير", "ar"),
    ),
    "volume": (
        ("hello world", "en"),
        ("blue sky", "en"),
        ("apple pie", "en"),
        ("good morning", "en"),
        ("foo bar baz", "en"),
        ("plain prose only", "en"),
        ("سماء زرقاء", "ar"),
        ("صباح الخير", "ar"),
    ),
    "amount_of_money": (
        ("hello world", "en"),
        ("rich and famous", "en"),
        ("blue sky", "en"),
        ("apple pie", "en"),
        ("foo bar baz", "en"),
        ("plain prose only", "en"),
        ("سماء زرقاء", "ar"),
        ("صباح الخير", "ar"),
    ),
    "email": (
        # Upstream Duckling's two ``negativeCorpus`` entries.
        ("hey@6", "en"),
        ("hey@you", "en"),
        # Common malformed-email shapes that must not parse.
        ("not-an-email", "en"),
        ("@nodomain", "en"),
        ("local@", "en"),
        ("multiple @ signs", "en"),
        ("hello world", "en"),
        ("just text", "en"),
    ),
    "url": (
        ("no url here", "en"),
        ("ftp something but not url", "en"),
        ("hello world", "en"),
        ("apple pie recipe", "en"),
        ("blue sky", "en"),
        ("foo bar baz", "en"),
    ),
    "phone_number": (
        ("abc-def-ghij", "en"),
        ("phone is missing", "en"),
        ("hello world", "en"),
        ("apple pie", "en"),
        ("blue sky", "en"),
        ("مرحبا بالعالم", "ar"),
        ("سماء زرقاء", "ar"),
    ),
    "credit_card": (
        # 16 digits in standard groupings but Luhn-invalid → must not match.
        ("1234 5678 9012 3456", "en"),
        ("abc def ghi jkl", "en"),
        ("hello world", "en"),
        ("apple pie recipe", "en"),
        ("0000 0000 0000 0000", "en"),
        ("9999 9999 9999 9999", "en"),
    ),
}


def _negative_cases() -> list[tuple[DimensionName, str, str]]:
    """Flatten ``NEGATIVE_BY_DIM`` into ``(dim, phrase, locale)`` triples."""
    return [
        (dim, phrase, locale)
        for dim, entries in NEGATIVE_BY_DIM.items()
        for phrase, locale in entries
    ]


@pytest.mark.parametrize("dim, phrase, locale", _negative_cases())
def test_negative_corpus(
    dim: DimensionName,
    phrase: str,
    locale: str,
    ctx_en: Context,
    ctx_ar: Context,
) -> None:
    ctx = ctx_en if locale == "en" else ctx_ar
    entities = parse(phrase, ctx, Options(), dims=(dim,))
    assert entities == [], (
        f"{phrase!r} unexpectedly produced {dim} entities: "
        f"{[(e.body, e.value) for e in entities]!r}"
    )
