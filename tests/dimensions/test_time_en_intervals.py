"""Corpus-driven tests for the supplemental English Time interval rules."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.time.en.intervals_corpus import CORPUS


def _matches(actual: dict, expected: dict) -> bool:
    """Loose dict-subset equality — same shape used by `test_time_en.py`."""
    return all(k in actual and actual[k] == v for k, v in expected.items())


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_intervals_corpus(phrase: str, expected: dict, ctx_en) -> None:
    entities = parse(phrase, ctx_en, Options(), dims=("time",))
    assert entities, f"no entity for {phrase!r}"
    assert any(_matches(e.value, expected) for e in entities), (
        f"{phrase!r} resolved to {[e.value for e in entities]}, expected {expected}"
    )
