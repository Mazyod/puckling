"""Public runtime value contract tests."""

from __future__ import annotations

import datetime as dt
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
from puckling.dimensions.time.types import (
    InstantValue,
    IntervalDirection,
    IntervalValue,
    OpenIntervalValue,
)


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


# ---------------------------------------------------------------------------
# TimeValue.start_datetime / end_datetime
#
# `primary` is a 3-way union (InstantValue | IntervalValue | OpenIntervalValue).
# Most callers want a single datetime ("when does this start?", "when does it
# end?") rather than write the same isinstance ladder repeatedly. These two
# helpers cover all four shapes — instant, closed interval, open-after (no
# upper bound), open-before (no lower bound) — and use `None` for the
# genuinely unbounded sides.


def _first_time_value(text: str, ctx) -> TimeValue:
    entities = parse(text, ctx, Options(), dims=("time",))
    for e in entities:
        if isinstance(e.value, TimeValue):
            return e.value
    raise AssertionError(f"no TimeValue parsed from {text!r}")


def test_start_datetime_for_instant(ctx_en):
    """An instant has a single value. `start_datetime` returns it; `end_datetime` is None."""
    v = _first_time_value("tomorrow at 5pm", ctx_en)
    assert isinstance(v.primary, InstantValue)
    assert v.start_datetime() == dt.datetime(2013, 2, 13, 17, 0, tzinfo=dt.UTC)
    assert v.end_datetime() is None


def test_start_and_end_datetime_for_closed_interval(ctx_en):
    """A closed interval anchored to absolute dates exposes both bounds."""
    v = _first_time_value("Feb 14 to Feb 16", ctx_en)
    assert isinstance(v.primary, IntervalValue)
    assert v.start_datetime() == dt.datetime(2013, 2, 14, tzinfo=dt.UTC)
    assert v.end_datetime() == dt.datetime(2013, 2, 16, tzinfo=dt.UTC)


def test_open_interval_before_has_only_end(ctx_en):
    """`before March` is upper-bounded — no start, only an end."""
    v = _first_time_value("before March", ctx_en)
    assert isinstance(v.primary, OpenIntervalValue)
    assert v.primary.direction is IntervalDirection.BEFORE
    assert v.start_datetime() is None
    assert v.end_datetime() == v.primary.instant.value


def test_open_interval_after_has_only_start(ctx_en):
    """`after March` is lower-bounded — start only, no end."""
    v = _first_time_value("after March", ctx_en)
    assert isinstance(v.primary, OpenIntervalValue)
    assert v.primary.direction is IntervalDirection.AFTER
    assert v.start_datetime() == v.primary.instant.value
    assert v.end_datetime() is None


def test_start_datetime_return_type_is_optional(ctx_en):
    """Static contract: helpers always return `dt.datetime | None`. Pyright
    enforces the union so callers can't forget the unbounded case."""
    v = _first_time_value("tomorrow at 5pm", ctx_en)
    assert_type(v.start_datetime(), dt.datetime | None)
    assert_type(v.end_datetime(), dt.datetime | None)
