"""Supplemental email tests — phrase variants and edge cases.

These tests complement ``test_email.py`` by exercising in-sentence emails,
trailing punctuation, multiple emails per phrase, and a handful of valid
local-part / domain shapes.
"""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.email.extra_corpus import (
    CORPUS,
    MULTI_EMAIL_CORPUS,
    NEGATIVE_CORPUS,
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_extra_corpus(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("email",))
    assert entities, f"no entity for {phrase!r}"
    assert expected in [e.value for e in entities]


@pytest.mark.parametrize("phrase, expected_emails", MULTI_EMAIL_CORPUS)
def test_multiple_emails_per_phrase(phrase, expected_emails, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("email",))
    bodies = {e.body for e in entities}
    for addr in expected_emails:
        assert addr in bodies, f"missing {addr!r} in {phrase!r} (got {bodies!r})"


@pytest.mark.parametrize("phrase", NEGATIVE_CORPUS)
def test_extra_negative_corpus(phrase, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("email",))
    assert not entities, f"unexpected entity for {phrase!r}: {entities!r}"


def test_trailing_period_is_not_part_of_email(ctx_en):
    """The regex requires ``[\\w_-]+`` after each dot, so a trailing period in a
    sentence (``...example.io.``) must stay outside the entity body."""
    entities = parse("My email is alice@exAmple.io.", ctx_en, Options(), dims=("email",))
    assert entities
    assert entities[0].body == "alice@exAmple.io"
