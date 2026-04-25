"""Ordinal value type."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OrdinalValue:
    """A parsed ordinal number (e.g. 1st, 2nd, الثاني)."""

    value: int
    latent: bool = False

    def resolve(self, _context: object) -> OrdinalValue:
        return self


def ordinal(value: int) -> OrdinalValue:
    return OrdinalValue(value=value)
