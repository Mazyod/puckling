"""Corpus tests for the supplemental Arabic time interval / numeric-date rules."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.time.ar.intervals_corpus import CORPUS
from tests.value_helpers import value_matches


def _matches(actual: dict, expected: dict) -> bool:
    return all(k in actual and actual[k] == v for k, v in expected.items())


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_intervals_corpus(phrase: str, expected: dict, ctx_ar) -> None:
    entities = parse(phrase, ctx_ar, Options(with_latent=True), dims=("time",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities), (
        f"{phrase!r} resolved to {[e.value for e in entities]}, expected {expected}"
    )


@pytest.mark.parametrize(
    "phrase",
    [
        "32/12",
        "31/13",
        "31/02/2013",
        "2013-02-31",
        "2013-13-01",
        "21/09/2013/05",
        "2013/04/04",
        "04-04-",
        "الرابع من",
        "بين 32/12 و 31/13",
        "من 25:00 / 26:00",
    ],
)
def test_negative_cases(phrase: str, ctx_ar) -> None:
    assert parse(phrase, ctx_ar, Options(with_latent=True), dims=("time",)) == []
