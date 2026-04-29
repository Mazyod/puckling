"""Corpus-driven tests for Arabic Duration."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.duration.ar.corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Malformed or partial unit words.
    "10 ساعهx",
    "10 دقيقا",
    "20 اسابيعه",
    "3 شهروات",
    "سنةة",
    # Unit substrings inside larger words.
    "اسبوعي",
    "دقيقةواحدة",
    "ساعةاليد",
    "المستشفى ساعةالزيارة",
    "ساعاتي الجديدة",
    "اليوم جميل",
    "الأيام جميلة",
    "أسبوعيات المجلة",
    "شهرياً",
    "سنواتي",
    "عاملة",
    "ثوانيه",
    "الساعة الآن الخامسة",
    # Missing numeric values for plural units, or missing units for numerals.
    "ساعات",
    "دقائق",
    "أيام",
    "اسابيع",
    "شهور",
    "سنوات",
    "5",
    "٣",
    "خمسة",
    "ثلاثة",
    # Prose with no duration expression.
    "هذا نص عربي عادي",
    "تم تحديث الطلب بنجاح",
    "الكتاب على الطاولة",
    "سأقرأ كتابا في المساء",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("duration",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_negative_cases(phrase, ctx_ar):
    assert parse(phrase, ctx_ar, Options(), dims=("duration",)) == []
