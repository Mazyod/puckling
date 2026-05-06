"""Corpus tests for AmountOfMoney AR."""

from __future__ import annotations

import pytest

from puckling import Context, Locale, Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.amount_of_money.ar.corpus import CORPUS
from puckling.locale import Lang, Region
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Malformed or partial currency words.
    "10 دولا",
    "10 دين",
    "10 دولارx",
    "هذا ليس 10 دولاريا",
    # Punctuation should not bridge symbols to numbers.
    "$،10",
    "$-10",
    "10،$",
    "10.$",
    "10,5 دولار",
    # Prose without a complete amount.
    "الدولار قوي اليوم",
    "سعر الدولار ارتفع",
    "فاتورة رقم 10 فقط",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("amount_of_money",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities), (
        f"phrase={phrase!r} expected={expected!r} got={[e.value for e in entities]!r}"
    )


def test_fils_decimal_parses_for_kuwait_locale(reference_time):
    ctx_kw = Context(reference_time=reference_time, locale=Locale(Lang.AR, Region.KW))
    entities = parse("0.750 فلس", ctx_kw, Options(), dims=("amount_of_money",))
    assert any(
        e.body == "0.750 فلس"
        and value_matches(e.value, {"value": 0.75, "unit": "fils", "type": "value"})
        for e in entities
    ), f"expected Kuwaiti fils amount; got {[(e.body, e.value) for e in entities]!r}"


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_negative_cases(phrase, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("amount_of_money",))
    assert entities == []


COMPARATOR_PHRASES: tuple[str, ...] = (
    "اكثر من 100 دينار",
    "أكثر من 100 دينار",
    "اقل من عشره دنانير",
    "اقل من 5 دنانير",
    "تقريبا 13 دينار",
    "تقريباً 13 دينار",
    "حوالي 50 دينار",
    "حوالى 50 دينار",
    "فوق 100 دينار",
    "دون 50 دينار",
    "قرابه 100 دينار",
    "قرابة 100 دينار",
    "قريب من 50 دينار",
)


@pytest.mark.parametrize("phrase", COMPARATOR_PHRASES)
def test_comparator_prefix_extends_body(phrase, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("amount_of_money",))
    assert entities, f"no entity for {phrase!r}"
    bodies = [e.body for e in entities]
    assert phrase in bodies, (
        f"expected body to include comparator for {phrase!r}; got {bodies!r}"
    )


def test_comparator_without_currency_yields_no_money(ctx_ar):
    entities = parse("اكثر من 5 ايام", ctx_ar, Options(), dims=("amount_of_money",))
    assert entities == []


def test_comparator_does_not_emit_duplicate_overlapping_money(ctx_ar):
    entities = parse(
        "اكثر من 100 دينار", ctx_ar, Options(), dims=("amount_of_money",)
    )
    money_entities = [e for e in entities if e.dim == "amount_of_money"]
    assert len(money_entities) == 1, (
        f"expected single amount-of-money entity; got {[(e.body, e.start, e.end) for e in money_entities]!r}"
    )
