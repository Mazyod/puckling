"""Corpus tests for the Arabic volume dimension."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.volume.ar.corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Unit aliases should not match inside larger Arabic words.
    "5 ملابس",
    "٥ملابس",
    "5 ملمع",
    "5 ميليار",
    "5 لتراث",
    "5 لترية",
    "5 جالونيا",
    "5 غالونيا",
    "5 هكتوليترية",
    # Malformed numeric/unit joins should not degrade into smaller valid spans.
    "5ملx",
    "5لترx",
    "5 لترx",
    "5ميليلترx",
    "5جالونx",
    "5غالوناتx",
    "5 ميلي-لتر",
    "5 مل-لتر",
    "٣..٥ لتر",
    "٣٫٫٥ لتر",
    "3,5 لتر",
    "3،5 لتر",
    "--٣ لتر",
    "طلب5 لتر",
    "س5 لتر",
    "5 لترس",
    "نصف لترية",
    "لترينيات",
    # Missing numeric or fractional values.
    "مل",
    "ملي لتر",
    "لتر",
    "لترات",
    "جالون",
    "غالون",
    "غالونات",
    "هكتوليتر",
    "هكتو ليتر",
    "نصف",
    "ربع",
    # Non-volume prose.
    "أضف الماء حسب الحاجة",
    "هذا الوعاء كبير",
    "عبوة ماء فارغة",
    "سعر اللتر تغير اليوم",
    "الجالون وحدة قياس قديمة",
    "رقم 5 فقط",
    "في 5 دقائق",
    "اشترينا خمس عبوات",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("volume",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_negative_cases(phrase, ctx_ar):
    assert parse(phrase, ctx_ar, Options(), dims=("volume",)) == []
