"""URL value type — locale-agnostic."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UrlValue:
    value: str
    domain: str | None = None
    latent: bool = False

    def resolve(self, _context: object) -> UrlValue:
        return self


def url(value: str, domain: str | None = None) -> UrlValue:
    return UrlValue(value=value, domain=domain)
