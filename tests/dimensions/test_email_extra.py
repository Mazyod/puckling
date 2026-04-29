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
from tests.value_helpers import value_matches


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_extra_corpus(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("email",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase, expected_emails", MULTI_EMAIL_CORPUS)
def test_multiple_emails_per_phrase(phrase, expected_emails, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("email",))
    bodies = {e.body for e in entities}
    for addr in expected_emails:
        assert addr in bodies, f"missing {addr!r} in {phrase!r} (got {bodies!r})"


@pytest.mark.parametrize("phrase", NEGATIVE_CORPUS)
def test_extra_negative_corpus(phrase, ctx_en):
    assert parse(phrase, ctx_en, Options(), dims=("email",)) == []


@pytest.mark.parametrize(
    ("phrase", "expected_body"),
    [
        ("My email is alice@exAmple.io.", "alice@exAmple.io"),
        ("My email is alice@exAmple.io,", "alice@exAmple.io"),
        ("hello, alice@exAmple.io!", "alice@exAmple.io"),
        ("Confirm alice@exAmple.io?", "alice@exAmple.io"),
        ("Use alice@exAmple.io;next", "alice@exAmple.io"),
        ("(yo+yo@blah.org)", "yo+yo@blah.org"),
        ("<1234+abc@x.net>", "1234+abc@x.net"),
        ('Quote: "jean-jacques@stuff.co.uk"', "jean-jacques@stuff.co.uk"),
    ],
)
def test_surrounding_punctuation_is_not_part_of_email(phrase, expected_body, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("email",))
    assert entities
    assert entities[0].body == expected_body
    assert value_matches(entities[0].value, {"value": expected_body, "type": "value"})
