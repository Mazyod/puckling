"""Public puckling API.

Mirrors Duckling's `Api.hs`:

    parse(text, context, options, dims) -> list[Entity]

`Context` carries the reference time and locale; `Options` carries options like
`with_latent`. `dims` filters which dimensions are returned.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, cast

from puckling.dimensions.amount_of_money.types import AmountOfMoneyValue
from puckling.dimensions.credit_card.types import CreditCardValue
from puckling.dimensions.distance.types import DistanceValue
from puckling.dimensions.duration.types import DurationValue
from puckling.dimensions.email.types import EmailValue
from puckling.dimensions.numeral.types import NumeralValue
from puckling.dimensions.ordinal.types import OrdinalValue
from puckling.dimensions.phone_number.types import PhoneNumberValue
from puckling.dimensions.quantity.types import QuantityValue
from puckling.dimensions.temperature.types import (
    TemperatureIntervalValue,
    TemperatureOpenIntervalValue,
    TemperatureValue,
)
from puckling.dimensions.time.types import TimeValue
from puckling.dimensions.url.types import UrlValue
from puckling.dimensions.volume.types import VolumeValue
from puckling.engine import (
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TIME_BUDGET_MS,
    parse_and_resolve,
)
from puckling.locale import Lang, Locale
from puckling.types import Range, Rule, Token

type DimensionName = Literal[
    "amount_of_money",
    "credit_card",
    "distance",
    "duration",
    "email",
    "numeral",
    "ordinal",
    "phone_number",
    "quantity",
    "temperature",
    "time",
    "url",
    "volume",
]

type TemperatureResolvedValue = (
    TemperatureValue | TemperatureIntervalValue | TemperatureOpenIntervalValue
)

# The union of every value type produced by a first-party dimension. Custom
# dimensions discovered via the registry surface their own value types
# unchanged at runtime — this alias documents what built-in dimensions return
# and is exported for callers that want to narrow with `isinstance`.
type ResolvedValue = (
    AmountOfMoneyValue
    | CreditCardValue
    | DistanceValue
    | DurationValue
    | EmailValue
    | NumeralValue
    | OrdinalValue
    | PhoneNumberValue
    | QuantityValue
    | TemperatureResolvedValue
    | TimeValue
    | UrlValue
    | VolumeValue
)


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
class Entity[ValueT]:
    """A surfaced parse result, ready for callers."""

    body: str
    dim: DimensionName
    value: ValueT
    start: int
    end: int
    latent: bool = False


@dataclass(frozen=True, slots=True)
class ResolvedEntity[ValueT]:
    """A resolved parse result before longest non-overlapping winner selection."""

    range: Range
    dim: DimensionName
    value: ValueT
    grain: str | None = None
    latent: bool = False


def parse(
    text: str,
    context: Context,
    options: Options | None = None,
    dims: tuple[DimensionName, ...] | None = None,
) -> list[Entity[ResolvedValue]]:
    """Parse `text` into a list of structured entities.

    Returns the longest non-overlapping set of resolved entities. Internal
    `regex_match` tokens are never surfaced. `dims`, if given, must contain
    only names returned by `supported_dimensions()`.
    """
    options = options or Options()
    validated = _validate_dims(dims)
    rules = _collect_rules(context.locale.lang, validated)
    tokens = parse_and_resolve(
        rules,
        text,
        max_iterations=options.max_iterations,
        time_budget_ms=options.parse_timeout_ms,
        max_tokens=options.max_tokens,
    )
    resolved = _resolve_tokens(tokens, context, options)
    if validated is not None:
        wanted = set(validated)
        resolved = [r for r in resolved if r.dim in wanted]
    return _select_winners(text, resolved)


def analyze(
    text: str,
    context: Context,
    options: Options | None = None,
    dims: tuple[DimensionName, ...] | None = None,
) -> list[ResolvedEntity[ResolvedValue]]:
    """Like `parse`, but returns the full set of resolved tokens (including overlaps)."""
    options = options or Options()
    validated = _validate_dims(dims)
    rules = _collect_rules(context.locale.lang, validated)
    tokens = parse_and_resolve(
        rules,
        text,
        max_iterations=options.max_iterations,
        time_budget_ms=options.parse_timeout_ms,
        max_tokens=options.max_tokens,
    )
    resolved = _resolve_tokens(tokens, context, options)
    if validated is not None:
        wanted = set(validated)
        resolved = [r for r in resolved if r.dim in wanted]
    return resolved


def supported_dimensions() -> tuple[str, ...]:
    """Return every dimension known to puckling."""
    from puckling.dimensions import _registry

    return _registry.known_dimensions()


# ---------------------------------------------------------------------------
# internals


def _validate_dims(
    dims: tuple[DimensionName, ...] | None,
) -> tuple[str, ...] | None:
    if dims is None:
        return None
    known = set(supported_dimensions())
    unknown = [d for d in dims if d not in known]
    if unknown:
        raise ValueError(
            f"Unknown dimension(s): {sorted(unknown)!r}. "
            f"Supported: {sorted(known)!r}"
        )
    return tuple(dims)


def _collect_rules(lang: Lang, dims: tuple[str, ...] | None) -> tuple[Rule, ...]:
    from puckling.dimensions import _registry

    return _registry.rules_for(lang, dims)


def _resolve_tokens(
    tokens: list[Token],
    context: Context,
    options: Options,
) -> list[ResolvedEntity[ResolvedValue]]:
    """Convert tokens into `Resolved` results, dropping regex tokens and (by default) latents."""
    out: list[ResolvedEntity[ResolvedValue]] = []
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
        raw_grain = getattr(tok.value, "grain", None)
        if isinstance(raw_grain, Enum) and isinstance(raw_grain.value, str):
            grain = raw_grain.value
        elif isinstance(raw_grain, str):
            grain = raw_grain
        else:
            grain = None
        dim = cast(DimensionName, tok.dim)
        out.append(
            ResolvedEntity(
                range=tok.range,
                dim=dim,
                value=cast(ResolvedValue, resolved_value),
                grain=grain,
                latent=latent,
            )
        )
    return out


def _resolve_value(value: object, context: Context) -> Any:
    """Run the value's `resolve(context)` if present; otherwise surface it as-is.

    Returns `None` only when a resolver explicitly returns `None`. Custom
    dimensions discovered by the registry pass through unchanged — the
    runtime does not enforce membership in `ResolvedValue`.
    """
    resolver = getattr(value, "resolve", None)
    if callable(resolver):
        return resolver(context)
    return value


def _select_winners(
    text: str,
    results: list[ResolvedEntity[ResolvedValue]],
) -> list[Entity[ResolvedValue]]:
    """Pick longest non-overlapping spans; ties go to the earlier match."""
    sorted_results = sorted(
        results,
        key=lambda r: (-(r.range.end - r.range.start), r.range.start),
    )
    chosen: list[ResolvedEntity[ResolvedValue]] = []
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
