"""Dimensions namespace.

Each dimension lives in `puckling.dimensions.<dim>/`. Locale-specific rules go
in `<dim>/<lang>/rules.py` exporting `RULES`. Locale-agnostic rules go in
`<dim>/rules.py`. The `_registry` module discovers and aggregates them.
"""

from puckling.dimensions import _registry

__all__ = ["_registry"]
