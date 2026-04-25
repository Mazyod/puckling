"""Corpus-driven tests for the Arabic phone number dimension."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.phone_number.ar.corpus import CORPUS


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("phone_number",))
    assert entities, f"no entity for {phrase!r}"
    assert expected in [e.value for e in entities]
