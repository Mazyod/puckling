"""Corpus-driven tests for English ordinals."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.ordinal.en.corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CORPUS: tuple[str, ...] = (
    # Malformed numeric suffixes.
    "1rd",
    "2st",
    "3nd",
    "4rd",
    "11st",
    "12nd",
    "13rd",
    "21th",
    "22st",
    "23nd",
    "101th",
    "111st",
    "112nd",
    "113rd",
    "1sth",
    "2ndd",
    "3rdth",
    "4thh",
    # Boundary traps: suffix-looking word endings are not ordinals.
    "best",
    "contest",
    "stand",
    "friend",
    "card",
    "bath",
    "birth",
    "smooth",
    # Larger words and identifiers must not expose an ordinal sub-span.
    "firstly",
    "firsthand account",
    "secondhand smoke",
    "thirdparty library",
    "fourthcoming typo",
    "sixthsense guess",
    "seventhly",
    "twentyfirstly",
    "ninetieths",
    "v1st",
    "1stchoice",
    "foo1st",
    "order2nd",
    "3rdparty",
    "4thcoming",
    "1st_place",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("ordinal",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase", NEGATIVE_CORPUS)
def test_negative_corpus(phrase, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("ordinal",))
    assert entities == [], f"unexpected entity for {phrase!r}: {entities!r}"
