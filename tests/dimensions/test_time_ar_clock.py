"""Corpus tests for the Arabic clock-time supplemental ruleset."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.time.ar.clock_corpus import CORPUS
from tests.value_helpers import value_matches


def _matches(actual: dict, expected: dict) -> bool:
    return all(k in actual and actual[k] == v for k, v in expected.items())


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_clock_corpus(phrase: str, expected: dict, ctx_ar) -> None:
    entities = parse(phrase, ctx_ar, Options(with_latent=True), dims=("time",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities), (
        f"{phrase!r} resolved to {[e.value for e in entities]}, expected {expected}"
    )


@pytest.mark.parametrize(
    "phrase",
    [
        "25:00",
        "24:00",
        "12:60",
        "3::20",
        "3:20:40",
        "0.10",
        "00.10",
        "$0.10",
        "٠.١٠",
        "0.10 من منو",
        "0.18 حق شنو",
        "الساعة 25",
        "الساعة 5 و 75 دقيقة",
        "الساعة الخامسة و ثلاثة",
        "الساعة الخامسة إلا خمس",
    ],
)
def test_negative_cases(phrase: str, ctx_ar) -> None:
    assert parse(phrase, ctx_ar, Options(with_latent=True), dims=("time",)) == []
