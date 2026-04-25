"""Corpus-driven tests for the supplemental EN Time relative + cycle rules."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.time.en.relative_corpus import CORPUS


def _matches(actual: dict, expected: dict) -> bool:
    """Loose dict-subset equality.

    A time entity carries optional alternates and metadata that the corpus does
    not always pin down; we accept any actual dict whose keys named in
    `expected` agree exactly. For nested dicts (interval `from`/`to`), recurse.
    """
    for k, v in expected.items():
        if k not in actual:
            return False
        if isinstance(v, dict) and isinstance(actual[k], dict):
            if not _matches(actual[k], v):
                return False
        elif actual[k] != v:
            return False
    return True


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_relative_corpus(phrase: str, expected: dict, ctx_en) -> None:
    entities = parse(phrase, ctx_en, Options(with_latent=True), dims=("time",))
    assert entities, f"no entity for {phrase!r}"
    assert any(_matches(e.value, expected) for e in entities), (
        f"{phrase!r} resolved to {[e.value for e in entities]}, expected {expected}"
    )
