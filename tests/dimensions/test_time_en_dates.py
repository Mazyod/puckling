"""Corpus-driven tests for the supplemental English Time date rules."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.time.en.dates_corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Malformed numeric dates should not surface a partial time value.
    "2013--02--12",
    "03//15//2014",
    "2013/00",
    "2013-00",
    "00/00/2013",
    "10/00/2013",
)


def _matches(actual: dict, expected: dict) -> bool:
    return all(k in actual and actual[k] == v for k, v in expected.items())


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_dates_corpus(phrase: str, expected: dict, ctx_en) -> None:
    entities = parse(phrase, ctx_en, Options(with_latent=True), dims=("time",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities), (
        f"{phrase!r} resolved to {[e.value for e in entities]}, expected {expected}"
    )


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_dates_negative_cases(phrase: str, ctx_en) -> None:
    assert parse(phrase, ctx_en, Options(), dims=("time",)) == []
