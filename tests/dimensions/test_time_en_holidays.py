"""Corpus-driven tests for the English Time dimension — supplemental holidays."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.time.en.holidays_corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Holiday-like prose and word prefixes/suffixes that are not holiday names.
    "holiday party",
    "memorialize day",
    "laboratory day",
    "independence invoice day",
    "flagship day",
    "mothership day",
    "groundhogging day",
    "turkey day sandwich",
)


def _matches(actual: dict, expected: dict) -> bool:
    return all(k in actual and actual[k] == v for k, v in expected.items())


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_holidays_corpus(phrase: str, expected: dict, ctx_en) -> None:
    entities = parse(phrase, ctx_en, Options(), dims=("time",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities), (
        f"{phrase!r} resolved to {[e.value for e in entities]}, expected {expected}"
    )


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_holidays_negative_cases(phrase: str, ctx_en) -> None:
    assert parse(phrase, ctx_en, Options(), dims=("time",)) == []
