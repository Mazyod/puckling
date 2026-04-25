"""Public runtime value contract tests."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import assert_type

import pytest

from puckling import (
    AmountOfMoneyValue,
    Entity,
    NumeralValue,
    Options,
    ResolvedEntity,
    ResolvedValue,
    TimeValue,
    analyze,
    parse,
)
from puckling.dimensions.time.types import InstantValue


def test_single_dimension_parse_returns_resolved_value(ctx_en):
    entities = parse("5", ctx_en, Options(), dims=("numeral",))
    assert_type(entities, list[Entity[ResolvedValue]])
    value = entities[0].value
    assert isinstance(value, NumeralValue)
    assert is_dataclass(value)
    assert asdict(value)["value"] == 5


def test_single_dimension_analyze_returns_resolved_value(ctx_en):
    entities = analyze("5", ctx_en, Options(), dims=("numeral",))
    assert_type(entities, list[ResolvedEntity[ResolvedValue]])
    assert any(isinstance(e.value, NumeralValue) for e in entities)

    positional_entities = analyze("5", ctx_en, Options(), ("numeral",))
    assert_type(positional_entities, list[ResolvedEntity[ResolvedValue]])


def test_time_parse_returns_nested_runtime_values(ctx_en):
    entities = parse("tomorrow at 5pm", ctx_en, Options(), dims=("time",))
    assert_type(entities, list[Entity[ResolvedValue]])
    value = entities[0].value
    assert isinstance(value, TimeValue)
    assert isinstance(value.primary, InstantValue)
    dumped = asdict(value)
    assert dumped["primary"]["grain"].value == "hour"
    assert dumped["primary"]["value"].isoformat() == "2013-02-13T17:00:00+00:00"


def test_default_parse_uses_resolved_value_union(ctx_en):
    entities = parse("$50 tomorrow", ctx_en, Options())
    assert_type(entities, list[Entity[ResolvedValue]])
    assert all(is_dataclass(entity.value) for entity in entities)


def test_money_value_asdict_is_pythonic(ctx_en):
    entities = parse("$50", ctx_en, Options(), dims=("amount_of_money",))
    assert_type(entities, list[Entity[ResolvedValue]])
    value = entities[0].value
    assert isinstance(value, AmountOfMoneyValue)
    dumped = asdict(value)
    assert dumped == {"value": 50, "currency": "USD", "latent": False}


def test_parse_rejects_unknown_dimension(ctx_en):
    with pytest.raises(ValueError, match="Unknown dimension"):
        parse("5", ctx_en, Options(), dims=("numerals",))  # pyright: ignore[reportArgumentType]


def test_analyze_rejects_unknown_dimension(ctx_en):
    with pytest.raises(ValueError, match="Unknown dimension"):
        analyze("5", ctx_en, Options(), dims=("nope",))  # pyright: ignore[reportArgumentType]
