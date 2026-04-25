"""Corpus tests for the supplemental Arabic time holidays + relative rules."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.time.ar.holidays_corpus import CORPUS
from tests.value_helpers import value_matches


def _matches(actual: dict, expected: dict) -> bool:
    return all(k in actual and actual[k] == v for k, v in expected.items())


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_holidays_corpus(phrase: str, expected: dict, ctx_ar) -> None:
    # Parts-of-day rules are `latent`; opt in so they surface as entities too.
    entities = parse(phrase, ctx_ar, Options(with_latent=True), dims=("time",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities), (
        f"{phrase!r} resolved to {[e.value for e in entities]}, expected {expected}"
    )
