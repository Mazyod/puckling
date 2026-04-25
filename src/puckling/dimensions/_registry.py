"""Auto-discover dimension subpackages and aggregate their RULES.

The registry walks `puckling.dimensions.*` subpackages. For each subpackage
`<dim>` and a requested `lang`, it tries:

    puckling.dimensions.<dim>.<lang>.rules:RULES   (locale-specific)
    puckling.dimensions.<dim>.rules:RULES          (locale-agnostic)

Whichever exist contribute their tuple of `Rule`s. Workers don't touch this
file — they just create the appropriate `rules.py` and the registry picks it up.
"""

from __future__ import annotations

import importlib
import pkgutil
from functools import cache

from puckling.locale import Lang
from puckling.types import Rule


def _candidates(dim: str, lang: Lang) -> tuple[str, ...]:
    return (
        f"puckling.dimensions.{dim}.{lang.value.lower()}.rules",
        f"puckling.dimensions.{dim}.rules",
    )


@cache
def known_dimensions() -> tuple[str, ...]:
    import puckling.dimensions as dims_pkg

    names = [info.name for info in pkgutil.iter_modules(dims_pkg.__path__) if info.ispkg]
    return tuple(sorted(names))


def rules_for(lang: Lang, dims: tuple[str, ...] | None) -> tuple[Rule, ...]:
    """Aggregate `RULES` across all dimensions (or only those in `dims`) for `lang`."""
    rules: list[Rule] = []
    targets = dims if dims is not None else known_dimensions()
    for dim in targets:
        for mod_name in _candidates(dim, lang):
            try:
                mod = importlib.import_module(mod_name)
            except ModuleNotFoundError:
                continue
            rules.extend(getattr(mod, "RULES", ()))
    return tuple(rules)
