"""Corpus-driven tests for Quantity EN."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.quantity.en.corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Malformed unit/product joins must not expose a valid unit prefix.
    "2 cupof sugar",
    "2 cupsugar",
    "2 gramsugar",
    "2 poundsign",
    "2 ouncesomething",
    "2 g/kg serving",
    "2 lb/ft mixture",
    # Unit names and abbreviations embedded in words.
    "3 cupcakes",
    "2 cupfuls",
    "2 gramophone needles",
    "2 gforce events",
    "2 g-string packs",
    "2 gsuite users",
    "1 lbtest",
    "2 ozark routes",
    # Missing numeric values or invalid article/plural shapes.
    "cups of sugar",
    "grams of flour",
    "pounds",
    "ounces",
    "cup",
    "gram",
    "lb",
    "oz",
    "of sugar",
    "a cups",
    "an grams",
    "a pounds",
    "an ounces",
    # Prose that mentions quantity words without a quantity value.
    "please add cup holders",
    "the cupcake recipe is simple",
    "the pound sign is #",
    "ounce of prevention",
    "gramophone music",
    "weights are in grams for the label",
    # Malformed numeric shapes must not degrade to a smaller valid span.
    "2..3 cups",
    "2,000 grams",
    "-2 cups",
    "+2 cups",
    "v2 cups",
    "2. cups",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("quantity",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities), (
        f"phrase={phrase!r} expected={expected!r} got={[e.value for e in entities]!r}"
    )


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_negative_cases(phrase, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("quantity",))
    assert entities == [], (
        f"{phrase!r} unexpectedly produced quantity entities: "
        f"{[(e.body, e.value) for e in entities]!r}"
    )
