"""Auto-discover dimension subpackages and aggregate their RULES.

The registry walks `puckling.dimensions.*` subpackages. For each subpackage
`<dim>` and a requested `lang`, it loads:

    puckling.dimensions.<dim>.<lang>.rules:RULES                 (locale-specific main)
    puckling.dimensions.<dim>.<lang>.<anything>_rules:RULES      (locale-specific supplement)
    puckling.dimensions.<dim>.rules:RULES                        (locale-agnostic main)
    puckling.dimensions.<dim>.<anything>_rules:RULES             (locale-agnostic supplement)

Supplemental `*_rules.py` files let workers extend a dimension without editing
the main `rules.py` (and without conflicting with siblings). Workers never edit
this file — they just create their `<topic>_rules.py` module and the registry
picks it up.
"""

from __future__ import annotations

import importlib
import pkgutil
from functools import cache, lru_cache

from puckling.locale import Lang
from puckling.types import Rule

# Cross-dimension rule dependencies. A dim's `<currency> <amount>`-style
# composition rules consume tokens produced by these other dims, so requesting
# only the surface dim and not its deps would silently drop legitimate
# matches (e.g. `$1/2` needs the numeral `fractional number` rule).
_DIM_DEPS: dict[str, tuple[str, ...]] = {
    "amount_of_money": ("numeral",),
    "distance": ("numeral",),
    "duration": ("numeral",),
    "quantity": ("numeral",),
    "temperature": ("numeral",),
    "time": ("numeral", "ordinal"),
    "volume": ("numeral",),
}


@cache
def known_dimensions() -> tuple[str, ...]:
    import puckling.dimensions as dims_pkg

    names = [info.name for info in pkgutil.iter_modules(dims_pkg.__path__) if info.ispkg]
    return tuple(sorted(names))


def _expand_with_deps(dims: tuple[str, ...]) -> tuple[str, ...]:
    """Return `dims` plus the transitive closure of `_DIM_DEPS`."""
    seen = set(dims)
    queue = list(dims)
    while queue:
        d = queue.pop()
        for dep in _DIM_DEPS.get(d, ()):
            if dep not in seen:
                seen.add(dep)
                queue.append(dep)
    return tuple(sorted(seen))


def _is_rules_module(name: str) -> bool:
    return name == "rules" or name.endswith("_rules")


def _import_rules_modules(pkg_name: str) -> list:
    """Return all submodules of `pkg_name` whose name is `rules` or `*_rules`."""
    out = []
    try:
        pkg = importlib.import_module(pkg_name)
    except ModuleNotFoundError:
        return out
    pkg_path = getattr(pkg, "__path__", None)
    if pkg_path is None:
        return out
    for info in pkgutil.iter_modules(pkg_path):
        if info.ispkg or not _is_rules_module(info.name):
            continue
        try:
            mod = importlib.import_module(f"{pkg_name}.{info.name}")
        except ModuleNotFoundError:
            continue
        out.append(mod)
    return out


@lru_cache(maxsize=64)
def rules_for(lang: Lang, dims: tuple[str, ...] | None) -> tuple[Rule, ...]:
    """Aggregate `RULES` across all dimensions (or only those in `dims`) for `lang`.

    Cached on `(lang, dims)`. The module set is static at runtime, so any
    workload that calls `parse()` repeatedly with the same locale + dim
    filter pays the import-machinery cost only once. Bounded as defense in
    depth — cardinality is `|Lang| × subsets-of-dims`, so `64` is generous.
    """
    rules: list[Rule] = []
    targets = _expand_with_deps(dims) if dims is not None else known_dimensions()
    lang_seg = lang.value.lower()
    for dim in targets:
        # Locale-specific submodules under <dim>/<lang>/
        for mod in _import_rules_modules(f"puckling.dimensions.{dim}.{lang_seg}"):
            rules.extend(getattr(mod, "RULES", ()))
        # Locale-agnostic submodules under <dim>/
        for mod in _import_rules_modules(f"puckling.dimensions.{dim}"):
            rules.extend(getattr(mod, "RULES", ()))
    return tuple(rules)
