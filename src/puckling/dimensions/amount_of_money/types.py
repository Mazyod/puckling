"""AmountOfMoney value type."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AmountOfMoneyValue:
    """An amount with a currency code (ISO-4217 where applicable)."""

    value: float | None
    currency: str | None
    latent: bool = False

    def resolve(self, _context: object) -> dict:
        out: dict = {"type": "value"}
        if self.value is not None:
            out["value"] = self.value
        if self.currency is not None:
            out["unit"] = self.currency
        return out


def money(value: float | None, currency: str | None) -> AmountOfMoneyValue:
    return AmountOfMoneyValue(value=value, currency=currency)
