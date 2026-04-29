"""Corpus tests for the English phone number dimension."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.phone_number.en.corpus import CORPUS
from tests.value_helpers import value_matches


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("phone_number",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize(
    "phrase",
    (
        "call 415--555-1212",
        "call 415..555.1212",
        "call 415//555//1212",
        "call 12345",
        "tracking number 123456789012345678901234",
        "call 1-234-567-8901-2345-6789",
        "email user4155551212@example.com",
        "open https://example.com/415-555-1212",
        "open https://example.com?phone=415-555-1212",
        "open https://5551212.example.com",
        "ticket ABC1234567 is pending",
        "invoice INV-4155551212 was archived",
        "Use 1234 for the door and 5678 for the alarm",
    ),
)
def test_negative_cases(phrase, ctx_en):
    assert parse(phrase, ctx_en, Options(), dims=("phone_number",)) == []


def test_phone_number_inside_sentence_with_punctuation(ctx_en):
    entities = parse("Call (415) 555-1212.", ctx_en, Options(), dims=("phone_number",))
    assert entities
    assert entities[0].body == "(415) 555-1212"
