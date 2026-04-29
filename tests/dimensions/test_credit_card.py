"""Tests for the locale-agnostic ``credit_card`` dimension."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.credit_card.corpus import CORPUS, NEGATIVE_CORPUS
from tests.value_helpers import value_matches

LOCAL_NEGATIVE_CASES: tuple[str, ...] = (
    # Luhn-invalid values, including the space-separated form puckling accepts
    # for valid cards.
    "4111 1111 1111 1110",
    "79927398710",
    "3530111333300001",
    # Malformed separators and separator-adjacent overmatches.
    "4111 1111-1111 1111",
    "3714 496353-98431",
    "6011-1111 1111-1117",
    "5555-5555 5555-4444",
    "3056-930902 5904",
    "4111-1111-1111-1111-",
    "4111-1111-1111-1111-0000",
    "4111 1111 1111",
    # Too-short/too-long digit runs.
    "4111111",
    "41111111111111111111",
    # Identifier adjacency must not surface an embedded valid card.
    "card4111111111111111",
    "4111111111111111suffix",
    "acct_4111111111111111",
    "4111111111111111_2026",
    # Plain prose and common numeric text that should not be a card.
    "my visa card expires tomorrow",
    "the card number field is required",
    "use card number xxxx xxxx xxxx xxxx",
    "call me at 555-555-5555",
    "invoice 1234 due on 5678",
)


AR_CONTEXT_NEGATIVE_CASES: tuple[str, ...] = (
    "بطاقة4111111111111111",
    "4111111111111111لاحقة",
    "بطاقتي 4111 1111-1111 1111",
    "رقم البطاقة مطلوب فقط",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus_en(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("credit_card",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus_ar(phrase, expected, ctx_ar):
    # The dimension is locale-agnostic; identical values should surface under AR.
    entities = parse(phrase, ctx_ar, Options(), dims=("credit_card",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase", NEGATIVE_CORPUS)
def test_negative_corpus_en(phrase, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("credit_card",))
    assert entities == [], f"unexpected entity for {phrase!r}: {entities!r}"


@pytest.mark.parametrize("phrase", LOCAL_NEGATIVE_CASES)
def test_local_negative_cases_en(phrase, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("credit_card",))
    assert entities == [], f"unexpected entity for {phrase!r}: {entities!r}"


@pytest.mark.parametrize("phrase", AR_CONTEXT_NEGATIVE_CASES)
def test_negative_cases_ar(phrase, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("credit_card",))
    assert entities == [], f"unexpected entity for {phrase!r}: {entities!r}"
