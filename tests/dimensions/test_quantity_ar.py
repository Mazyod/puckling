"""Corpus-driven tests for Arabic quantity rules."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.quantity.ar.corpus import CORPUS


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("quantity",))
    assert entities, f"no entity for {phrase!r}"
    assert expected in [e.value for e in entities], (
        f"phrase={phrase!r} expected={expected!r} got={[e.value for e in entities]!r}"
    )
