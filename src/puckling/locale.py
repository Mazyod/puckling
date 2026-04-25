"""Locale model for puckling. Only English and Arabic are supported."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Lang(Enum):
    """Supported languages (ISO-639-1)."""

    EN = "EN"
    AR = "AR"


class Region(Enum):
    """ISO-3166 alpha-2 region codes that can pair with a `Lang`.

    Region is informational; v1 of puckling does not split rules by region.
    """

    US = "US"
    GB = "GB"
    AU = "AU"
    CA = "CA"
    EG = "EG"
    SA = "SA"
    AE = "AE"
    KW = "KW"


@dataclass(frozen=True, slots=True)
class Locale:
    """A language plus optional region."""

    lang: Lang
    region: Region | None = None

    def __str__(self) -> str:
        if self.region is None:
            return self.lang.value
        return f"{self.lang.value}_{self.region.value}"


SUPPORTED_LANGS: tuple[Lang, ...] = (Lang.EN, Lang.AR)
