"""Corpus-driven tests for Arabic quantity rules."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.quantity.ar.corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Malformed or partial unit/product phrases.
    "3 من السكر",
    "500 من الفراولة",
    "5 كيلو",
    "5 ميلي",
    "5 ك غ",
    "5 غ را م",
    "3 اكو اب",
    "3 اكوابمن السكر",
    "5 غراممن السكر",
    "5 كغمن السكر",
    # Unit aliases should not match inside larger Arabic words.
    "جمبري",
    "جمهور",
    "غمامة",
    "5 جمبري",
    "5 غمامة",
    "5 كوبري",
    "5 أكوابية",
    "5 باوندية",
    "5 اونصاتية",
    "5 ملغومة",
    "5 كغماء",
    "5 كجمية",
    # Missing numeric/unit values.
    "من السكر",
    "من الفراولة",
    "كيلو من السكر",
    "كمية من السكر",
    # Non-quantity Arabic prose.
    "هذا النص عربي فقط",
    "أحتاج كمية مناسبة من السكر",
    "اشتريت السكر من السوق",
    "الذهب باهظ الثمن",
    "الكوب على الطاولة",
    "الغرام وحدة كتلة",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("quantity",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities), (
        f"phrase={phrase!r} expected={expected!r} got={[e.value for e in entities]!r}"
    )


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_negative_cases(phrase, ctx_ar):
    assert parse(phrase, ctx_ar, Options(), dims=("quantity",)) == []
