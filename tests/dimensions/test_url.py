"""Tests for the URL dimension (locale-agnostic)."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.url.corpus import CORPUS, NEGATIVE_CORPUS


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus_en(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("url",))
    assert entities, f"no entity for {phrase!r}"
    assert expected in [e.value for e in entities]


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus_ar(phrase, expected, ctx_ar):
    # URL is locale-agnostic — should work under AR too.
    entities = parse(phrase, ctx_ar, Options(), dims=("url",))
    assert entities, f"no entity for {phrase!r}"
    assert expected in [e.value for e in entities]


@pytest.mark.parametrize("phrase", NEGATIVE_CORPUS)
def test_negative_corpus(phrase, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("url",))
    assert not entities, f"unexpected url entity for {phrase!r}: {entities!r}"
