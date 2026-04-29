"""Corpus-driven tests for the Arabic phone number dimension."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.phone_number.ar.corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Malformed separators and parentheses should not yield partial phones.
    "050--123--4567",
    "+965 5012--3456",
    "+965 5012_3456",
    "+ 965 5012 3456",
    "+965- 5012 3456",
    "(02 1234 5678",
    "02) 1234 5678",
    "٠٥٠--١٢٣٤--٥٦٧٨",
    # Too-short or too-long digit runs.
    "12345",
    "١٢٣٤٥",
    "1234 56",
    "05012345678901234",
    "٠٥٠١٢٣٤٥٦٧٨٩٠١٢٣٤",
    # Arabic prose with non-phone digit snippets.
    "عندي 12345 كتاب",
    "وصلت سنة 2024 وفي الساعة 1234",
    "رقم الطلب ١٢٣٤٥ قيد المعالجة",
    "رمز التحقق 1234 صالح لدقيقتين",
    # Identifiers should not surface embedded phone-looking substrings.
    "INV0501234567",
    "abc0501234567def",
    "رقم_0501234567",
    "طلب-5012-3456",
    # URL/email-adjacent strings should stay out of phone_number.
    "https://example.com/0501234567",
    "example.com/0501234567",
    "www.0501234567.com",
    "0501234567.com",
    "user0501234567@example.com",
    "user@example.com0501234567",
    "0501234567@example.com",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("phone_number",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_negative_cases(phrase, ctx_ar):
    assert parse(phrase, ctx_ar, Options(), dims=("phone_number",)) == []
