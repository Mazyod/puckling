"""Corpus tests for AmountOfMoney AR."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.amount_of_money.ar.corpus import CORPUS
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


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_negative_cases(phrase, ctx_ar):
    entities = parse(phrase, ctx_ar, Options(), dims=("amount_of_money",))
    assert entities == []
