"""Corpus-driven tests for Arabic Temperature."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.temperature.ar.corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Unit words without a numeric value.
    "°",
    "درجة",
    "درجات",
    "درجه",
    "درجة مئوية",
    "مئوية",
    "سلزيوس",
    "سيليسيوس",
    "فهرنهايت",
    "تحت الصفر",
    # Weather prose without an explicit temperature.
    "الجو حار اليوم",
    "الطقس بارد جدا",
    "درجة الحرارة مرتفعة",
    "الحرارة عالية",
    "انخفضت الحرارة مساء",
    # Malformed degree and numeric tokens should not degrade into subspans.
    "٣٠٫ درجة",
    "٣٠. درجة",
    "٣٠..٥ درجة",
    "٣٠٫٫٥ درجة",
    "٣٠°°",
    "٣٠ ° °",
    "٣٠-درجة",
    "٣٠/درجة",
    "--٢ درجة",
    "٣٠ درجةمئوية",
    # Boundary traps around embedded digits and suffix-attached units.
    "س٣٠ درجة",
    "٣٠ درجةس",
    "رقم٣٠ درجة",
    "abc30 درجة",
    "30 درجةabc",
    "٣٠درجة",
    "٣٠ سلزيوسx",
    "٣٠ فهرنهايتx",
    "٣٠°سx",
    "درجتينx",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("temperature",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_negative_cases(phrase, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("temperature",))
    assert entities == [], (
        f"{phrase!r} unexpectedly produced temperature entities: "
        f"{[(e.body, e.value) for e in entities]!r}"
    )
