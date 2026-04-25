"""Credit card value type — locale-agnostic."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreditCardValue:
    value: str
    issuer: str | None = None
    latent: bool = False

    def resolve(self, _context: object) -> CreditCardValue:
        return self


def credit_card(value: str, issuer: str | None = None) -> CreditCardValue:
    return CreditCardValue(value=value, issuer=issuer)
