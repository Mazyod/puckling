"""URL value type — locale-agnostic."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UrlValue:
    value: str
    domain: str | None = None
    latent: bool = False

    def resolve(self, _context: object) -> dict:
        out = {"value": self.value, "type": "value"}
        if self.domain is not None:
            out["domain"] = self.domain
        return out


def url(value: str, domain: str | None = None) -> UrlValue:
    return UrlValue(value=value, domain=domain)
