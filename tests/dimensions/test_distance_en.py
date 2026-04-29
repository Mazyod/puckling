"""Corpus-driven tests for Distance EN."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.distance.en.corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES = (
    # Unit abbreviations embedded in words.
    "the admin set 3kmode",
    "print 5inside labels",
    "there are 3milestones",
    "tighten A4mm bolts",
    # Malformed numeric/unit joins or compound units.
    "ship 3kg today",
    "plot 3 km2 parcels",
    "measure .3 km later",
    "walk 3..5 km",
    "run 3km/h",
    "run 3 km/h",
    # Direction/geography prose.
    "book 3 miami hotels",
    "take route 66 east",
    "exit onto 2 north street",
    "follow I-95 north",
    # Unsupported range/open-interval distance shapes.
    "between 3 and 5 kilometers",
    "3-5 km",
    "5-6 mm",
    "3 to 5 km",
    "from 3 to 5 km",
    "from 3km to 5km",
    "about 3km-5km",
    "under 3.5 miles",
    "at least 5''",
    "more than 5 inches",
    "less than 2 meters",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("distance",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities), (
        f"expected {expected!r} in {[e.value for e in entities]!r} for {phrase!r}"
    )


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_negative_cases(phrase, ctx_en):
    assert parse(phrase, ctx_en, Options(), dims=("distance",)) == []
