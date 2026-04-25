"""Tests for the email dimension."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.email.corpus import CORPUS, NEGATIVE_CORPUS
from tests.value_helpers import value_matches


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("email",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase", NEGATIVE_CORPUS)
def test_negative_corpus(phrase, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("email",))
    assert not entities, f"unexpected entity for {phrase!r}: {entities!r}"


def test_email_is_locale_agnostic(ctx_ar):
    """The single email rule lives outside any locale subfolder, so it must fire under AR too."""
    entities = parse("alice@example.io", ctx_ar, Options(), dims=("email",))
    assert entities
    assert value_matches(entities[0].value, {"value": "alice@example.io", "type": "value"})


def test_email_within_sentence(ctx_en):
    entities = parse("Email me at test@example.com please", ctx_en, Options(), dims=("email",))
    assert entities
    assert value_matches(entities[0].value, {"value": "test@example.com", "type": "value"})
    assert entities[0].body == "test@example.com"
