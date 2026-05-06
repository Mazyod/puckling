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
    # Partial currency words are prose, not money.
    "10 usdollars",
    "10 dollarstore",
    "50 centennial",
    # Note: `10,000 dollars`, `20-30 dollars`, `$20-$30`, `USD - 20`, and
    # `20..30 USD` were previously listed here but they expose
    # range/comma/decimal parses that align with upstream Duckling once the
    # numeral rules participate in the parse forest. They are no longer
    # asserted as rejections.
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


COMPARATOR_CASES: tuple[tuple[str, str], ...] = (
    ("more than 200 kwd", "more than 200 kwd"),
    ("less than 100 kwd", "less than 100 kwd"),
    ("over 2500 kwd", "over 2500 kwd"),
    ("around 50 dollars", "around 50 dollars"),
    ("about 100 kwd", "about 100 kwd"),
    ("up to 500 kwd", "up to 500 kwd"),
    ("approximately 75 dollars", "approximately 75 dollars"),
    ("at least 100 usd", "at least 100 usd"),
    ("at most 100 usd", "at most 100 usd"),
    ("under 50 dollars", "under 50 dollars"),
    ("above 50 dollars", "above 50 dollars"),
    ("below 50 dollars", "below 50 dollars"),
    ("roughly 50 kwd", "roughly 50 kwd"),
    ("a 50 kwd transfer", "a 50 kwd"),
)


@pytest.mark.parametrize("phrase, expected_body", COMPARATOR_CASES)
def test_comparator_prefix_widens_span(phrase, expected_body, ctx_en):
    entities = parse(phrase, ctx_en, Options(), dims=("amount_of_money",))
    assert entities, f"no entity for {phrase!r}"
    bodies = {e.body for e in entities}
    assert expected_body in bodies, (
        f"phrase={phrase!r} expected body containing comparator {expected_body!r}, got {bodies!r}"
    )


def test_cover_does_not_match_over_inside_word(ctx_en):
    """`over` must not match word-internally inside `cover`."""
    entities = parse("cover 50 kwd", ctx_en, Options(), dims=("amount_of_money",))
    assert entities, "expected money entity for `cover 50 kwd`"
    bodies = {e.body for e in entities}
    assert "50 kwd" in bodies, f"expected `50 kwd` body, got {bodies!r}"
    for body in bodies:
        assert "cover" not in body.lower(), (
            f"`cover` should not be absorbed as comparator, got body={body!r}"
        )


def test_bare_a_does_not_produce_money(ctx_en):
    """The article `a` must not fire on prose without a currency-bearing amount."""
    assert parse("a quick task", ctx_en, Options(), dims=("amount_of_money",)) == []
    assert parse("a", ctx_en, Options(), dims=("amount_of_money",)) == []
