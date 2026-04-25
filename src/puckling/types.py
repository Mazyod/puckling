"""Core types for puckling, faithfully translating Duckling's parsing model.

All types are frozen dataclasses; productions and predicates are pure functions.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import regex as _regex


@dataclass(frozen=True, slots=True)
class Range:
    """Closed-open span [start, end) into the source text."""

    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass(frozen=True, slots=True)
class RegexMatch:
    """The value carried by tokens produced by a `RegexItem`."""

    text: str
    groups: tuple[str | None, ...]


@dataclass(frozen=True, slots=True)
class Token:
    """A token in the parse forest.

    `dim` is the dimension name (e.g. "numeral", "time", "regex_match").
    `value` is the dimension-specific frozen value object.
    `range` is the source span; populated by the engine.
    `produced_by` is the rule name that emitted this token; populated by the engine.
    """

    dim: str
    value: Any
    range: Range = field(default=Range(0, 0))
    produced_by: str | None = None


# A predicate decides if a token can match a slot in a pattern.
Predicate = Callable[[Token], bool]


@dataclass(frozen=True, slots=True)
class RegexItem:
    """A pattern slot that matches a regex against the source text."""

    pattern: str
    flags: int = 0
    compiled: _regex.Pattern[str] | None = None

    def __post_init__(self) -> None:
        if self.compiled is None:
            import regex as _regex

            object.__setattr__(
                self,
                "compiled",
                _regex.compile(self.pattern, flags=self.flags | _regex.IGNORECASE | _regex.UNICODE),
            )


@dataclass(frozen=True, slots=True)
class PredicateItem:
    """A pattern slot that matches an existing token via a predicate."""

    fn: Predicate
    name: str = "predicate"


PatternItem = RegexItem | PredicateItem
Pattern = tuple[PatternItem, ...]


# A production transforms matched tokens into a new token (or None to reject).
Production = Callable[[tuple[Token, ...]], Token | None]


@dataclass(frozen=True, slots=True)
class Rule:
    """A grammar rule: name + sequence of pattern items + production function."""

    name: str
    pattern: Pattern
    prod: Production


@dataclass(frozen=True, slots=True)
class Resolved:
    """A fully resolved parse result, ready to surface to callers."""

    range: Range
    dim: str
    value: Any
    grain: str | None = None
    latent: bool = False


def regex(pattern: str, flags: int = 0) -> RegexItem:
    """Helper to build a `RegexItem` (Duckling's `regex` constructor)."""
    return RegexItem(pattern=pattern, flags=flags)


def predicate(fn: Predicate, name: str = "predicate") -> PredicateItem:
    """Helper to build a `PredicateItem`."""
    return PredicateItem(fn=fn, name=name)
