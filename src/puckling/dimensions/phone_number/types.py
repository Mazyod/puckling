"""Phone number value type."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PhoneNumberValue:
    value: str
    latent: bool = False

    def resolve(self, _context: object) -> PhoneNumberValue:
        return self


def phone(value: str) -> PhoneNumberValue:
    return PhoneNumberValue(value=value)
