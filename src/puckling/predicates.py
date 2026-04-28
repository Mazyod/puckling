"""Reusable predicates for cross-rule and cross-dimension composition.

Cross-dimension references in rule patterns go through these predicates rather
than direct imports — that keeps each dimension's rule file independent of its
siblings, so they can be ported in parallel.
"""

from __future__ import annotations

from collections.abc import Callable

from puckling.types import Predicate, Token

_EXACT_DIM_ATTR = "__puckling_exact_dim__"


def _with_exact_dim(fn: Predicate, dim: str) -> Predicate:
    setattr(fn, _EXACT_DIM_ATTR, dim)
    return fn


def is_dim(name: str) -> Predicate:
    """Match any token of the given dimension name."""

    def go(t: Token) -> bool:
        return t.dim == name

    return _with_exact_dim(go, name)


def has_attr(attr: str, value: object) -> Predicate:
    """Match tokens whose value has `attr == value`."""

    def go(t: Token) -> bool:
        return getattr(t.value, attr, _SENTINEL) == value

    return go


def value_predicate(fn: Callable[[object], bool]) -> Predicate:
    """Lift a value-level predicate into a token predicate."""

    def go(t: Token) -> bool:
        return fn(t.value)

    return go


def is_numeral(t: Token) -> bool:
    return t.dim == "numeral"


def is_ordinal(t: Token) -> bool:
    return t.dim == "ordinal"


def is_time(t: Token) -> bool:
    return t.dim == "time"


def is_duration(t: Token) -> bool:
    return t.dim == "duration"


def is_grain(t: Token) -> bool:
    return t.dim == "time_grain"


def is_natural(t: Token) -> bool:
    """Whole, non-negative integer numerals."""
    if t.dim != "numeral":
        return False
    v = getattr(t.value, "value", None)
    return isinstance(v, int) and v >= 0


def is_positive(t: Token) -> bool:
    if t.dim != "numeral":
        return False
    v = getattr(t.value, "value", None)
    return isinstance(v, (int, float)) and v >= 0


def is_integer(t: Token) -> bool:
    if t.dim != "numeral":
        return False
    v = getattr(t.value, "value", None)
    return isinstance(v, int) or (isinstance(v, float) and v.is_integer())


def number_between(low: float, high: float) -> Predicate:
    """Numeral with `low <= value < high`."""

    def go(t: Token) -> bool:
        if t.dim != "numeral":
            return False
        v = getattr(t.value, "value", None)
        if not isinstance(v, (int, float)):
            return False
        return low <= v < high

    return go


def number_equal_to(target: float) -> Predicate:
    def go(t: Token) -> bool:
        if t.dim != "numeral":
            return False
        v = getattr(t.value, "value", None)
        return isinstance(v, (int, float)) and v == target

    return go


def one_of(values: tuple[float, ...]) -> Predicate:
    """Numeral whose value matches one of `values`."""
    s = set(values)

    def go(t: Token) -> bool:
        if t.dim != "numeral":
            return False
        v = getattr(t.value, "value", None)
        return v in s

    return go


def is_multipliable(t: Token) -> bool:
    """A numeral that carries a magnitude grain (hundred/thousand/million)."""
    if t.dim != "numeral":
        return False
    return bool(getattr(t.value, "multipliable", False))


_SENTINEL = object()

_with_exact_dim(is_numeral, "numeral")
_with_exact_dim(is_ordinal, "ordinal")
_with_exact_dim(is_time, "time")
_with_exact_dim(is_duration, "duration")
_with_exact_dim(is_grain, "time_grain")
