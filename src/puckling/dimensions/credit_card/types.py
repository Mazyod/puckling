"""Credit card value type — locale-agnostic."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreditCardValue:
    value: str
    issuer: str | None = None
    latent: bool = False

    def resolve(self, _context: object) -> dict:
        out = {"value": self.value, "type": "value"}
        if self.issuer is not None:
            out["issuer"] = self.issuer
        return out


def credit_card(value: str, issuer: str | None = None) -> CreditCardValue:
    return CreditCardValue(value=value, issuer=issuer)
