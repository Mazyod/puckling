"""Foundation engine tests — proves saturation, regex, predicates, range tracking."""

from __future__ import annotations

from puckling.dimensions.numeral.types import NumeralValue
from puckling.engine import parse_and_resolve
from puckling.predicates import is_numeral, number_between
from puckling.types import Range, Rule, Token, regex


def _digit_rule() -> Rule:
    """A regex-leading rule: matches any digit run, emits a Numeral token."""

    def prod(tokens: tuple[Token, ...]) -> Token | None:
        match = tokens[0].value.text
        return Token(dim="numeral", value=NumeralValue(value=int(match)))

    return Rule(name="digits", pattern=(regex(r"\d+"),), prod=prod)


def _adjacent_pair_rule() -> Rule:
    """A predicate-leading rule: two adjacent numerals produce their sum."""
    from puckling.types import predicate as pred_item

    def prod(tokens: tuple[Token, ...]) -> Token | None:
        a, b = tokens[0].value.value, tokens[1].value.value
        return Token(dim="numeral", value=NumeralValue(value=a + b))

    return Rule(
        name="sum",
        pattern=(pred_item(is_numeral, "is_numeral"), pred_item(is_numeral, "is_numeral")),
        prod=prod,
    )


def test_engine_parses_single_regex_match():
    rules = (_digit_rule(),)
    out = parse_and_resolve(rules, "the number 42 was found")
    nums = [t for t in out if t.dim == "numeral"]
    # Engine produces every match (including the partial "2" inside "42");
    # winner selection happens in the API layer. The longest match must be present.
    longest = max(nums, key=lambda t: t.range.length)
    assert longest.value.value == 42
    assert longest.range.start == 11
    assert longest.range.end == 13


def test_engine_parses_multiple_regex_matches():
    rules = (_digit_rule(),)
    out = parse_and_resolve(rules, "1 then 22 then 333")
    nums = [t for t in out if t.dim == "numeral"]
    values = {t.value.value for t in nums}
    # Every full-length match must be produced by the engine.
    assert {1, 22, 333} <= values


def test_engine_saturates_predicate_rules():
    rules = (_digit_rule(), _adjacent_pair_rule())
    out = parse_and_resolve(rules, "10 20")
    nums = sorted([t for t in out if t.dim == "numeral"], key=lambda t: (t.range.start, t.range.end))
    values = sorted({n.value.value for n in nums})
    assert 10 in values and 20 in values
    assert 30 in values  # produced by the predicate-leading rule


def test_engine_dedupes_identical_tokens():
    rules = (_digit_rule(),)
    out_one = parse_and_resolve(rules, "5 5")
    twos = [t for t in out_one if t.dim == "numeral" and t.value.value == 5]
    assert len(twos) == 2  # different ranges, both kept


def test_engine_terminates_on_empty_input():
    rules = (_digit_rule(),)
    assert parse_and_resolve(rules, "") == []


def test_number_between_predicate():
    rules = (_digit_rule(),)
    out = parse_and_resolve(rules, "1 50 99 100")
    matches = [t for t in out if t.dim == "numeral" and number_between(50, 100)(t)]
    values = sorted(t.value.value for t in matches)
    assert values == [50, 99]


def test_engine_assigns_correct_ranges():
    rules = (_digit_rule(),)
    text = "abc 42 def"
    out = parse_and_resolve(rules, text)
    nums = [t for t in out if t.dim == "numeral"]
    longest = max(nums, key=lambda t: t.range.length)
    assert longest.range == Range(4, 6)
    assert text[longest.range.start : longest.range.end] == "42"
