"""Quantity value type."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QuantityValue:
    value: float
    unit: str
    product: str | None = None
    latent: bool = False

    def resolve(self, _context: object) -> QuantityValue:
        return self


def quantity(value: float, unit: str, product: str | None = None) -> QuantityValue:
    return QuantityValue(value=value, unit=unit, product=product)
