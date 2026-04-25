"""Quantity value type."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QuantityValue:
    value: float
    unit: str
    product: str | None = None
    latent: bool = False

    def resolve(self, _context: object) -> dict:
        out = {"value": self.value, "unit": self.unit, "type": "value"}
        if self.product is not None:
            out["product"] = self.product
        return out


def quantity(value: float, unit: str, product: str | None = None) -> QuantityValue:
    return QuantityValue(value=value, unit=unit, product=product)
