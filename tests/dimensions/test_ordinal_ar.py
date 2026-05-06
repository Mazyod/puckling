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
    # Indefinite ثاني/ثانيه means "another/other" in banking dialect, not ordinal.
    "بنك ثاني",
    "تلفون ثاني",
    "احد ثاني",
    "ثاني",
    "ثاني يوم",
    "ثانيه",
    "بطاقه ثانيه",
    "مره ثانيه",
)


DEFINITE_ORDINAL_EXAMPLES = (
    ("الثاني", 2),
    ("الثانيه", 2),
    ("الثانية", 2),
    ("الشخص الثاني", 2),
    ("اليوم الثاني", 2),
    ("الثالث", 3),
    ("الرابع", 4),
    ("الخامس", 5),
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


@pytest.mark.parametrize("phrase, expected_value", DEFINITE_ORDINAL_EXAMPLES)
def test_definite_ordinals_still_fire(phrase, expected_value, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("ordinal",))
    assert entities, f"no ordinal entity for {phrase!r}"
    assert any(
        value_matches(e.value, {"value": expected_value, "type": "ordinal"})
        for e in entities
    ), f"no ordinal({expected_value}) for {phrase!r}: {entities!r}"
