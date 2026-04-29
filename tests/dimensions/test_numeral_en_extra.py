"""Corpus-driven tests for the supplemental English Numeral phrase variants."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.numeral.en.extra_corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Malformed signs without a following numeral.
    "-",
    "--",
    "---",
    "+",
    "++",
    "+-",
    "-+",
    "minus",
    "negative",
    "minus -",
    "negative -",
    # Malformed decimal markers without digits.
    ".",
    "..",
    "...",
    "point",
    "dot",
    "point point",
    "dot dot",
    "point dot",
    "dot point",
    # Malformed fractions without numeric numerator/denominator.
    "/",
    "//",
    "///",
    " / ",
    " / / ",
    # Word-boundary traps: number words embedded in ordinary words.
    "stone",
    "alone",
    "money",
    "someone",
    "phone",
    "done",
    "tone",
    "nonevent",
    "thousandfold",
    "millionaire",
    "billionaire",
    "hundredweight",
    "twentyish",
    "fiftyfold",
    "twofold",
    "fourteeners",
    "fewest",
    "coupled",
    "pairing",
    # Ordinary prose that resembles number grammar but carries no numeral.
    "the phone rang",
    "done deal",
    "standalone build",
    "nonevent happened",
    "a millionaires club",
    "twentyish people",
    "negative sentiment",
    "minus sign only",
    "point taken",
    "dot matrix",
    "coupled service",
    "pairing mode",
    "fewest wins",
    "fivefold increase",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_extra_corpus(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("numeral",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_extra_negative_cases(phrase, ctx_en):
    assert parse(phrase, ctx_en, Options(), dims=("numeral",)) == []
