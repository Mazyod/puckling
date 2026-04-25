"""Email value type — locale-agnostic."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EmailValue:
    value: str
    latent: bool = False

    def resolve(self, _context: object) -> EmailValue:
        return self


def email(value: str) -> EmailValue:
    return EmailValue(value=value)
