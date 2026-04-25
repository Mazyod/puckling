"""Corpus-driven tests for the supplemental English Time clock rules."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.time.en.clock_corpus import CORPUS


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
    assert any(_matches(e.value, expected) for e in entities), (
        f"{phrase!r} resolved to {[e.value for e in entities]}, expected {expected}"
    )
