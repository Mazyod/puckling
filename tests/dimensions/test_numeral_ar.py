"""Corpus-driven tests for the Arabic numeral dimension."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.numeral.ar.corpus import CORPUS
from tests.value_helpers import value_matches


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("numeral",))
    assert entities, f"no entity for {phrase!r}"
    values = [e.value for e in entities]
    assert any(value_matches(value, expected) for value in values), (
        f"{phrase!r} resolved to {values}, expected {expected}"
    )
