"""Corpus tests for Arabic ordinal parsing."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.ordinal.ar.corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_EXAMPLES = (
    "أو",
    "الأو",
    "اولويات",
    "الأولويات",
    "الثالثون",
    "ثالثا",
    "الخامسون",
    "ثانوي",
    "العاشرية",
    "هذا نص عربي عادي",
    "الكتاب على الطاولة",
    "ذهبت إلى السوق صباحا",
    "الأحد  عشر",
    "الحادي  عشر",
    "الاثنى  عشر",
    "الأولاد",
    "الاولاد",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("ordinal",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase", NEGATIVE_EXAMPLES)
def test_negative_examples(phrase, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("ordinal",))
    assert entities == [], f"unexpected entity for {phrase!r}: {entities!r}"
