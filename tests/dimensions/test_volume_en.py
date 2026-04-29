"""Corpus-driven tests for English Volume."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.volume.en.corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Unit aliases and names embedded inside larger words.
    "the 3galaxy photos",
    "queue 2litigation tickets",
    "the 2 literate students",
    "take 1mlb lineup",
    "ship 250mlscript files",
    "add 3galloping notes",
    "order 3 galsx today",
    "the 3 hectoliterish samples",
    "pour 3 litters",
    # Malformed numeric/unit joins or unsupported compound shapes.
    "v2l release",
    "room2l label",
    "fill 2l2 bottles",
    "pour .5 liters",
    "pour 3..5 liters",
    "pour 3-5 liters",
    "pour 3 to 5 liters",
    "between 3 and 5 liters",
    "under 3.5 gallons",
    "more than 5 ml",
    "pour 3 l/100km",
    "pour 3 l / 100km",
    "pour 3 liters/second",
    "pour 3 liters / second",
    # Units or fractional words without a numeric volume.
    "liter",
    "liters",
    "l",
    "ml",
    "milliliter",
    "gallon",
    "hectoliters",
    "around gallons",
    "half",
    "half a",
    "quarter of",
    "tenth of a",
    # Ordinary prose that should not surface volume entities.
    "literature review",
    "the litigation hold",
    "mlb lineup",
    "gallonage labels",
    "hectoliters are rare",
    "one question about water",
    "we need more volume",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("volume",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_negative_cases(phrase, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("volume",))
    assert entities == [], f"unexpected volume entity for {phrase!r}: {entities!r}"
