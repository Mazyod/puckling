"""Corpus tests for the English phone number dimension."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.phone_number.en.corpus import CORPUS


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("phone_number",))
    assert entities, f"no entity for {phrase!r}"
    assert expected in [e.value for e in entities]
