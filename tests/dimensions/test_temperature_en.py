"""Corpus-driven pytest harness for the EN Temperature dimension."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.temperature.en.corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Unit markers without a numeric temperature.
    "°",
    "°C",
    "°F",
    "degree",
    "degrees",
    "deg.",
    "c",
    "celsius",
    "f",
    "fahrenheit",
    "degrees celsius",
    "degrees fahrenheit",
    # Qualitative temperature words are not temperature values on their own.
    "hot",
    "warm",
    "cold",
    "very hot",
    "warm weather",
    "cold outside",
    # Malformed or duplicated Celsius/Fahrenheit tokens must not parse a prefix.
    "37cc",
    "37ff",
    "37cf",
    "37fc",
    "37celsiusish",
    "37fahrenheitish",
    "37°Celsiusish",
    "70°Fahrenheitish",
    "37°cc",
    "70°ff",
    "37 C..",
    "37 F..",
    "37 °°C",
    "70 °°F",
    # Boundary traps: embedded identifiers and malformed numeric shapes.
    "room37C",
    "sensor_70F",
    "37Croom",
    "70F2",
    "10,000 degrees",
    "20..30 C",
    "+37C",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("temperature",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_negative_cases(phrase, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("temperature",))
    assert entities == [], f"unexpected temperature entity for {phrase!r}: {entities!r}"
