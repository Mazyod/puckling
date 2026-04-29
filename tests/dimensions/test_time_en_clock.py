"""Corpus-driven tests for the supplemental English Time clock rules."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.time.en.clock_corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Invalid numeric clock values.
    "24:60",
    "23:61",
    "5:60",
    "0pm",
    "00pm",
    # Malformed clock punctuation or unsupported clock wording.
    "call at 9:7",
    "5::30",
    "5..30pm",
    "0.10",
    "00.10",
    "$0.10",
    "0.10 dollars",
    "at 5xm",
    "half past 25",
    "quarter to 25",
)


def _matches(actual: dict, expected: dict) -> bool:
    """Loose dict-subset equality.

    Resolved time entities can carry optional alternates and metadata that the
    corpus does not always pin down. We accept any actual dict whose keys
    listed in `expected` agree exactly.
    """
    return all(k in actual and actual[k] == v for k, v in expected.items())


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_clock_corpus(phrase: str, expected: dict, ctx_en) -> None:
    entities = parse(phrase, ctx_en, Options(), dims=("time",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities), (
        f"{phrase!r} resolved to {[e.value for e in entities]}, expected {expected}"
    )


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_clock_negative_cases(phrase: str, ctx_en) -> None:
    assert parse(phrase, ctx_en, Options(), dims=("time",)) == []
