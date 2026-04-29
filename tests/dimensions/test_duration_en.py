"""Corpus-driven tests for English Duration."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.duration.en.corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CORPUS: tuple[str, ...] = (
    # Malformed units must not expose a valid unit prefix.
    "2 secondz",
    "2 minsx",
    "2 hrz",
    "2 dayz",
    "2 weekz",
    "2 monthz",
    "2 yearz",
    "2 qtrsx",
    "2 mo",
    "2 minuts",
    "2 houres",
    "2 mnths",
    "2 yrsx",
    "2 ms",
    "2 mm",
    "2 hh",
    # Compact abbreviations are valid, but not inside identifiers or words.
    "1secondhand",
    "2morrow",
    "2minnow",
    "2hoursglass",
    "2yearbook",
    "v2m",
    "room2m",
    "2miles",
    "2mm bolt",
    "2ms latency",
    "1.5 hertz",
    # Incomplete quantity/modifier/fraction phrases.
    "2 more",
    "2 additional",
    "2 extra",
    "2 less",
    "2 fewer",
    "about 2",
    "exactly two",
    "1/2",
    "half",
    "half a",
    "one and",
    "one and a",
    # Prose and word forms that should not be durations.
    "minutes from the meeting",
    "hourly report",
    "seconds before launch? no number",
    "one daydream",
    "we need more information",
    "additional context only",
    "less is more",
    "fewer issues today",
    "amazing result",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("duration",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities), (
        f"phrase={phrase!r} expected={expected!r} got={[e.value for e in entities]!r}"
    )


@pytest.mark.parametrize("phrase", NEGATIVE_CORPUS)
def test_negative_corpus(phrase, ctx_en):
    assert parse(phrase, ctx_en, Options(), dims=("duration",)) == []
