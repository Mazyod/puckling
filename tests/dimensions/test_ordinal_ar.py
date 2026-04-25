"""Corpus tests for Arabic ordinal parsing."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.ordinal.ar.corpus import CORPUS


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("ordinal",))
    assert entities, f"no entity for {phrase!r}"
    assert expected in [e.value for e in entities]
