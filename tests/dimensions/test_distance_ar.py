"""Corpus-driven tests for the Arabic distance dimension."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.distance.ar.corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Unit aliases should not match inside larger Arabic words.
    "5 كمبيوترات",
    "٥كمبيوتر",
    "5 سمكة",
    "5 ممرات",
    "5 ممثلين",
    "5 ميلادي",
    "5 قدماء",
    "5 انشغال",
    "5 كيلومترية",
    "5 مترية",
    # Malformed or partial unit phrases.
    "5 كيلو",
    "5 كيلو  متر",
    "5 كيلو-متر",
    "5 سنتي",
    "5 ميلي",
    "5 يار دة",
    "5 قد م",
    "5 بوص",
    "5 ك م",
    "5 س م",
    # Missing numerals.
    "كم",
    "كيلومتر",
    "متر",
    "أمتار",
    "سم",
    "مم",
    "ميل",
    "ياردة",
    "قدم",
    "بوصة",
    "إنش",
    # Non-distance prose.
    "هذا الطريق طويل",
    "المسافة قصيرة",
    "وصلنا بسرعة",
    "رقم 5 فقط",
    "في 5 دقائق",
    "5 سنوات",
    "طلب5 كم",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("distance",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_negative_cases(phrase, ctx_ar):
    assert parse(phrase, ctx_ar, Options(), dims=("distance",)) == []
