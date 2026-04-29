"""Tests for the URL dimension (locale-agnostic)."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.url.corpus import AR_CONTEXT_NEGATIVE_CORPUS, CORPUS, NEGATIVE_CORPUS
from tests.value_helpers import value_matches


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus_en(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("url",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus_ar(phrase, expected, ctx_ar):
    # URL is locale-agnostic — should work under AR too.
    entities = parse(phrase, ctx_ar, Options(), dims=("url",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase", NEGATIVE_CORPUS)
def test_negative_corpus_en(phrase, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("url",))
    assert entities == []


@pytest.mark.parametrize("phrase", AR_CONTEXT_NEGATIVE_CORPUS)
def test_negative_corpus_ar(phrase, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("url",))
    assert entities == []
