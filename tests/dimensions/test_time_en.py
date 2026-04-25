"""Corpus-driven tests for the English Time dimension."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.time.en.corpus import CORPUS
from tests.value_helpers import value_matches


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
