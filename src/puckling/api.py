"""Public puckling API.

Mirrors Duckling's `Api.hs`:

    parse(text, context, options, dims) -> list[Entity]

`Context` carries the reference time and locale; `Options` carries options like
`with_latent`. `dims` filters which dimensions are returned.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

from puckling.engine import (
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TIME_BUDGET_MS,
    parse_and_resolve,
)
from puckling.locale import Lang, Locale
from puckling.types import Resolved, Rule, Token


@dataclass(frozen=True, slots=True)
class Context:
    """Parse-time context. Reference time is the "now" used for relative dates."""

    reference_time: dt.datetime
    locale: Locale


@dataclass(frozen=True, slots=True)
class Options:
    """Parse options.

    `parse_timeout_ms` and `max_tokens` cap the engine to prevent runaway
    parses on pathological inputs. Pass `parse_timeout_ms=None` to disable
    the wall-clock cap (useful for offline corpus runs).
    """

    with_latent: bool = False
    max_iterations: int = DEFAULT_MAX_ITERATIONS
    parse_timeout_ms: int | None = DEFAULT_TIME_BUDGET_MS
    max_tokens: int = DEFAULT_MAX_TOKENS


@dataclass(frozen=True, slots=True)
class Entity:
    """A surfaced parse result, ready for callers."""

    body: str
    dim: str
    value: Any
    start: int
    end: int
    latent: bool = False


def parse(
    text: str,
    context: Context,
    options: Options | None = None,
    dims: tuple[str, ...] | None = None,
) -> list[Entity]:
    """Parse `text` into a list of structured entities.

    Returns the longest non-overlapping set of resolved entities. Internal
    `regex_match` tokens are never surfaced.
    """
    options = options or Options()
    rules = _collect_rules(context.locale.lang, dims)
    tokens = parse_and_resolve(
        rules,
        text,
        max_iterations=options.max_iterations,
        time_budget_ms=options.parse_timeout_ms,
        max_tokens=options.max_tokens,
    )
    resolved = _resolve_tokens(tokens, context, options)
    if dims is not None:
        wanted = set(dims)
        resolved = [r for r in resolved if r.dim in wanted]
    return _select_winners(text, resolved)


def analyze(
    text: str,
    context: Context,
    options: Options | None = None,
    dims: tuple[str, ...] | None = None,
) -> list[Resolved]:
    """Like `parse`, but returns the full set of resolved tokens (including overlaps)."""
    options = options or Options()
    rules = _collect_rules(context.locale.lang, dims)
    tokens = parse_and_resolve(
        rules,
        text,
        max_iterations=options.max_iterations,
        time_budget_ms=options.parse_timeout_ms,
        max_tokens=options.max_tokens,
    )
    resolved = _resolve_tokens(tokens, context, options)
    if dims is not None:
        wanted = set(dims)
        resolved = [r for r in resolved if r.dim in wanted]
    return resolved


def supported_dimensions() -> tuple[str, ...]:
    """Return every dimension known to puckling."""
    from puckling.dimensions import _registry

    return _registry.known_dimensions()


# ---------------------------------------------------------------------------
# internals


def _collect_rules(lang: Lang, dims: tuple[str, ...] | None) -> tuple[Rule, ...]:
    from puckling.dimensions import _registry

    return _registry.rules_for(lang, dims)


def _resolve_tokens(
    tokens: list[Token],
    context: Context,
    options: Options,
) -> list[Resolved]:
    """Convert tokens into `Resolved` results, dropping regex tokens and (by default) latents."""
    out: list[Resolved] = []
    for tok in tokens:
        if tok.dim in {"regex_match", "time_grain"}:
            continue
        latent = bool(getattr(tok.value, "latent", False))
        if latent and not options.with_latent:
            continue
        # Dimensions can opt-in to context-aware resolution by exposing
        # `value.resolve(context)`; otherwise the value is surfaced as-is.
        resolved_value = _resolve_value(tok.value, context)
        if resolved_value is None:
            continue
        grain = getattr(tok.value, "grain", None)
        if hasattr(grain, "value"):
            grain = grain.value
        out.append(
            Resolved(
                range=tok.range,
                dim=tok.dim,
                value=resolved_value,
                grain=grain if isinstance(grain, str) else None,
                latent=latent,
            )
        )
    return out


def _resolve_value(value: Any, context: Context) -> Any:
    resolver = getattr(value, "resolve", None)
    if callable(resolver):
        return resolver(context)
    return value


def _select_winners(text: str, results: list[Resolved]) -> list[Entity]:
    """Pick longest non-overlapping spans; ties go to the earlier match."""
    sorted_results = sorted(
        results,
        key=lambda r: (-(r.range.end - r.range.start), r.range.start),
    )
    chosen: list[Resolved] = []
    occupied: list[tuple[int, int]] = []
    for r in sorted_results:
        s, e = r.range.start, r.range.end
        if any(not (e <= os or s >= oe) for (os, oe) in occupied):
            continue
        chosen.append(r)
        occupied.append((s, e))
    chosen.sort(key=lambda r: r.range.start)
    return [
        Entity(
            body=text[r.range.start : r.range.end],
            dim=r.dim,
            value=r.value,
            start=r.range.start,
            end=r.range.end,
            latent=r.latent,
        )
        for r in chosen
    ]
