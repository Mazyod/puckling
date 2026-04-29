"""Corpus tests for AmountOfMoney/EN."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.amount_of_money.en.corpus import CORPUS
from tests.value_helpers import value_matches

NEGATIVE_CASES: tuple[str, ...] = (
    # Bare currency mentions are intermediate grammar tokens, not resolved money.
    "$",
    "paid in dollars",
    "the USD index rose",
    # Malformed symbol/code shapes should not degrade into a smaller valid span.
    "$$10",
    "€€20",
    "U$10",
    "$-20",
    "USD - 20",
    # Partial currency words are prose, not money.
    "10 usdollars",
    "10 dollarstore",
    "50 centennial",
    # Unsupported numeric/range shapes must not partially parse as money.
    "10,000 dollars",
    "20..30 USD",
    "20-30 dollars",
    "$20-$30",
)


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase, expected, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("amount_of_money",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities), (
        f"phrase={phrase!r} expected={expected!r} got={[e.value for e in entities]!r}"
    )


@pytest.mark.parametrize("phrase", NEGATIVE_CASES)
def test_negative_cases(phrase, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("amount_of_money",))
    assert entities == [], (
        f"{phrase!r} unexpectedly produced amount_of_money entities: "
        f"{[(e.body, e.value) for e in entities]!r}"
    )
