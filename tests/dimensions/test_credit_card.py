"""Tests for the locale-agnostic ``credit_card`` dimension."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.credit_card.corpus import CORPUS, NEGATIVE_CORPUS
from tests.value_helpers import value_matches


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("credit_card",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase", NEGATIVE_CORPUS)
def test_negative_corpus(phrase, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("credit_card",))
    assert entities == [], f"unexpected entity for {phrase!r}: {entities!r}"


def test_corpus_under_arabic_locale(ctx_ar):
    # The dimension is locale-agnostic; identical results must surface under AR.
    entities = parse("4111111111111111", ctx_ar, Options(), dims=("credit_card",))
    assert entities, "credit_card should also match under AR locale"
    assert value_matches(
        entities[0].value,
        {"value": "4111111111111111", "issuer": "visa", "type": "value"},
    )
