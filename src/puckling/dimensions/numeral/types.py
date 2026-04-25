"""Numeral value type."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NumeralValue:
    """A parsed cardinal number.

    `value` is the numeric value (int or float).
    `grain` is the log10 magnitude when this token represents a multiplier
    (hundred → 2, thousand → 3, million → 6); used for compositional rules.
    `multipliable` flags this token as eligible to be the right operand in
    multiplication composition (e.g. "five hundred").
    `latent` is unused for numerals; included for API uniformity.
    """

    value: int | float
    grain: int | None = None
    multipliable: bool = False
    latent: bool = False

    def resolve(self, _context: object) -> dict:
        return {"value": self.value, "type": "value"}


def numeral(value: int | float, *, grain: int | None = None, multipliable: bool = False) -> NumeralValue:
    return NumeralValue(value=value, grain=grain, multipliable=multipliable)
