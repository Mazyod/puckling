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
    "الأيام جميلة",
    "أسبوعيات المجلة",
    "شهرياً",
    "سنواتي",
    "عاملة",
    "ثوانيه",
    # `اليوم جميل` and `الساعة الآن الخامسة` previously asserted no duration,
    # but upstream Duckling does emit `يوم`/`ساعة` durations from the
    # bare grain word with the `ال` definite article in production data.
    # The proclitic-aware boundary brings parity.
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
    # Bare singular unit nouns acting as noun classifiers, not durations.
    # Duckling does not emit duration entities for these in production text;
    # the bare-singular tokens are kept latent so other rules (prefix +
    # duration → time) can compose them but the API does not surface them.
    "كم صرفت في سنه",
    "خلال سنه",
    "بسنه",
    "صرف خلال سنه 2025",
    "كل شهر نقاط معينه",
    "في اي شهر اخذت راتب",
    "تم تحويل الكشوفات قبل ساعه",
    "حابه وديعه ساعه",
    "كم دقيقه تستغرق العمليه",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_ar):
    # Bare singular unit nouns (ساعة / شهر / اسبوع / ...) are emitted as
    # latent durations so they don't pollute production output; opt into
    # latent here to test the duckling-corpus equivalence.
    entities = parse(phrase, ctx_ar, Options(with_latent=True), dims=("duration",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities)


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_negative_cases(phrase, ctx_ar):
    assert parse(phrase, ctx_ar, Options(), dims=("duration",)) == []


GLUED_CASES: tuple[tuple[str, dict], ...] = (
    ("24ساعه", {"value": 24, "unit": "hour"}),
    ("12شهر", {"value": 12, "unit": "month"}),
    ("3اشهر", {"value": 3, "unit": "month"}),
    ("5دقائق", {"value": 5, "unit": "minute"}),
    ("7ايام", {"value": 7, "unit": "day"}),
)


@pytest.mark.parametrize("phrase, expected", GLUED_CASES)
def test_glued_digit_unit(phrase, expected, ctx_ar):
    """Numeric and unit glued without space (e.g. `24ساعه`) must parse the
    same as the spaced form (`24 ساعه`).
    """
    entities = parse(phrase, ctx_ar, Options(), dims=("duration",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities), (
        f"phrase={phrase!r} expected={expected!r} got={[e.value for e in entities]!r}"
    )
