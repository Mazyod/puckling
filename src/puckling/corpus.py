"""Corpus test framework — declarative examples translated from Duckling's `Corpus.hs`.

A corpus is a list of `Example(value, [phrase, ...])` entries. The default
`run_corpus` driver parses each phrase under a fixed reference time and asserts
that the longest match's value equals the example's expected value.

Workers building a dimension's corpus.py should expose:

    CORPUS: tuple[Example, ...]
    REFERENCE_TIME: datetime  # optional; defaults to Duckling's canonical time

And then `tests/dimensions/test_<dim>_<locale>.py` does:

    from puckling.dimensions.<dim>.<lang>.corpus import CORPUS
    from puckling.corpus import pytest_examples

    @pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
    def test_corpus(phrase, expected, ctx_<lang>): ...
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

# Duckling's canonical reference time: 2013-02-12T04:30:00 UTC, Tuesday.
REFERENCE_TIME = dt.datetime(2013, 2, 12, 4, 30, 0, tzinfo=dt.UTC)


@dataclass(frozen=True, slots=True)
class Example:
    """A corpus entry: an expected value plus the phrases that should resolve to it."""

    value: Any
    phrases: tuple[str, ...]


def examples(value: Any, phrases: Iterable[str]) -> Example:
    """Mirror Duckling's `examples (V x) [...]` constructor."""
    return Example(value=value, phrases=tuple(phrases))


def pytest_examples(
    corpus: Iterable[Example],
) -> list[tuple[str, Any]]:
    """Flatten a corpus into (phrase, expected_value) pairs for pytest parametrization."""
    out: list[tuple[str, Any]] = []
    for ex in corpus:
        for phrase in ex.phrases:
            out.append((phrase, ex.value))
    return out


def assert_corpus(
    corpus: Iterable[Example],
    parse_one: Callable[[str], Any],
) -> None:
    """Drive a corpus through a single-phrase parser, asserting each example resolves."""
    for ex in corpus:
        for phrase in ex.phrases:
            actual = parse_one(phrase)
            assert actual == ex.value, (
                f"corpus mismatch: phrase={phrase!r} expected={ex.value!r} got={actual!r}"
            )
