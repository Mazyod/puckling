"""puckling — a Python port of Facebook's Duckling for English and Arabic."""

from __future__ import annotations

from puckling.api import (
    Context,
    Entity,
    Options,
    analyze,
    parse,
    supported_dimensions,
)
from puckling.locale import Lang, Locale, Region

__all__ = [
    "Context",
    "Entity",
    "Lang",
    "Locale",
    "Options",
    "Region",
    "analyze",
    "parse",
    "supported_dimensions",
]

__version__ = "0.1.0"
