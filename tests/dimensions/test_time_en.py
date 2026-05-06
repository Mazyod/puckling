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
    # Word-boundary leaks: short month/weekday/now/atm aliases must not match
    # inside longer English words like money / monthly / know / married /
    # decline / statement (mis-typed "statment") / friend / market / primary.
    "how to transfer money",
    "monthly subscription",
    "i want to know my balance",
    "knowing where to start",
    "married couples joint account",
    "marriage saving plan",
    "money market subscriptions",
    "primary device",
    "transaction declined",
    "keeps declining",
    "estatment of account",
    "i need a statment",
    "send link to my friend",
    "are you accepting africans for a loan",
    "wadi3a in nintendo",
    "abdul@1987 password",
    "is my pin 7298",
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


# Hijri month coverage — Ramadan family is the documented production gap
# (~281 EN parity rows). Mirrors duckling's month-grained Ramadan entity.
RAMADAN_BODIES: tuple[str, ...] = (
    "ramadan",
    "RAMADAN",
    "Ramadan",
    "ramadhan",
    "ramzan",
    "ramathan",
)


@pytest.mark.parametrize("phrase", RAMADAN_BODIES)
def test_ramadan_family_emits_time(phrase: str, ctx_en) -> None:
    entities = parse(phrase, ctx_en, Options(), dims=("time",))
    assert entities, f"no entity for {phrase!r}"
    assert any(e.body.lower() == phrase.lower() for e in entities)


@pytest.mark.parametrize("phrase", ("in ramadan", "during ramadhan"))
def test_in_during_ramadan_composes(phrase: str, ctx_en) -> None:
    entities = parse(phrase, ctx_en, Options(), dims=("time",))
    assert entities, f"no entity for {phrase!r}"
    assert any(e.body == phrase for e in entities)


def test_ramadan_year_composes(ctx_en) -> None:
    entities = parse("ramadan 2025", ctx_en, Options(), dims=("time",))
    assert entities, "no entity for 'ramadan 2025'"
    assert any(e.body == "ramadan 2025" for e in entities)


@pytest.mark.parametrize("phrase", ("ramadanik", "ramazani"))
def test_ramadan_word_boundary_negatives(phrase: str, ctx_en) -> None:
    assert parse(phrase, ctx_en, Options(), dims=("time",)) == []
