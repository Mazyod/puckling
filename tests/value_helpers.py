from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from puckling import ResolvedValue
from puckling.dimensions.duration.types import DurationValue
from puckling.dimensions.temperature.types import (
    TemperatureIntervalDirection,
    TemperatureIntervalValue,
    TemperatureOpenIntervalValue,
    TemperatureValue,
)
from puckling.dimensions.time.types import (
    InstantValue,
    IntervalDirection,
    IntervalValue,
    OpenIntervalValue,
    TimeValue,
)


def value_matches(actual: ResolvedValue, expected: Any) -> bool:
    """Compare a runtime value object against the legacy corpus expectation shape."""
    return _matches(_legacy_dump(actual), expected)


def values_contain(values: list[ResolvedValue], expected: Any) -> bool:
    return any(value_matches(value, expected) for value in values)


def _matches(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        for key, value in expected.items():
            if key not in actual:
                return False
            if not _matches(actual[key], value):
                return False
        return True
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            _matches(a, e) for a, e in zip(actual, expected, strict=True)
        )
    return actual == expected


def _legacy_dump(value: ResolvedValue) -> dict[str, Any]:
    if isinstance(value, TimeValue):
        return value.to_dict()
    if isinstance(value, DurationValue):
        return {
            "value": value.value,
            "unit": value.grain.value,
            "type": "value",
            "normalized": asdict(value.normalized),
        }
    if isinstance(value, TemperatureIntervalValue):
        return {
            "type": "interval",
            "from": _temperature_bound(value.start),
            "to": _temperature_bound(value.end),
        }
    if isinstance(value, TemperatureOpenIntervalValue):
        key = "from" if value.direction is TemperatureIntervalDirection.ABOVE else "to"
        return {"type": "interval", key: _temperature_bound(value.bound)}
    if not is_dataclass(value):
        raise TypeError(f"not a dataclass value: {value!r}")
    raw = asdict(value)
    out: dict[str, Any] = {"type": "value"}
    for key, item in raw.items():
        if key == "latent":
            continue
        if key == "currency":
            key = "unit"
        out[key] = _normalize(item)
    if "unit" in out and out["unit"] is None:
        out.pop("unit")
    if "issuer" in out and out["issuer"] is None:
        out.pop("issuer")
    if "domain" in out and out["domain"] is None:
        out.pop("domain")
    if "product" in out and out["product"] is None:
        out.pop("product")
    if "grain" in out and out["grain"] is None:
        out.pop("grain")
    if value.__class__.__name__ == "OrdinalValue":
        out["type"] = "ordinal"
    return out


def _temperature_bound(value: TemperatureValue) -> dict[str, Any]:
    out: dict[str, Any] = {"value": value.value}
    if value.unit is not None:
        out["unit"] = value.unit.value
    return out


def _normalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    return value


def time_instant(value: TimeValue) -> InstantValue:
    primary = value.primary
    assert isinstance(primary, InstantValue)
    return primary


def time_interval(value: TimeValue) -> IntervalValue:
    primary = value.primary
    assert isinstance(primary, IntervalValue)
    return primary


def time_open_interval(value: TimeValue) -> OpenIntervalValue:
    primary = value.primary
    assert isinstance(primary, OpenIntervalValue)
    return primary


def open_interval_legacy_key(value: OpenIntervalValue) -> str:
    return "to" if value.direction is IntervalDirection.BEFORE else "from"
