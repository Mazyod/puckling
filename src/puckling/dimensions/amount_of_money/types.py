"""AmountOfMoney value type."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AmountOfMoneyValue:
    """An amount with a currency code (ISO-4217 where applicable)."""

    value: int | float | None
    currency: str | None
    latent: bool = False

    def resolve(self, _context: object) -> AmountOfMoneyValue:
        return self


def money(value: int | float | None, currency: str | None) -> AmountOfMoneyValue:
    return AmountOfMoneyValue(value=value, currency=currency)
