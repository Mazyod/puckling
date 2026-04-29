"""Corpus-driven tests for the English Time dimension."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.time.en.corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Ordinary prose containing time-domain words should stay non-temporal.
    "we need to revisit the timeline",
    "please schedule the repository cleanup",
    "the sprint retrospective went well",
    "time flies when tests run",
    "clockwise sorting is enabled",
    "date parsing is complicated",
    "holiday mode is off",
    "interval training improves stamina",
    "relative imports are fragile",
)


def _matches(actual: dict, expected: dict) -> bool:
    """Loose dict-subset equality.

    A time entity carries optional alternates and metadata that the corpus
    does not always pin down. We accept any actual dict whose keys named in
    `expected` agree exactly.
    """
    return all(k in actual and actual[k] == v for k, v in expected.items())


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase: str, expected: dict, ctx_en) -> None:
    entities = parse(phrase, ctx_en, Options(), dims=("time",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities), (
        f"{phrase!r} resolved to {[e.value for e in entities]}, expected {expected}"
    )


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_negative_cases(phrase: str, ctx_en) -> None:
    assert parse(phrase, ctx_en, Options(), dims=("time",)) == []
