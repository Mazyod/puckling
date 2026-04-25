"""Arabic time — supplemental rules for intervals, DD/MM dates, ordinal-DOM.

Augments the base AR Time ruleset with:
- Closed intervals: "بين X و Y", "من X إلى Y", "من X حتى Y", "X - Y", "X إلى Y".
- Open intervals: "قبل X" / "حتى X" (before), "بعد X" / "منذ X" (after).
- Numeric date forms: "DD/MM", "DD-MM-YYYY", "DD/MM/YYYY", "YYYY-MM-DD".
- Ordinal day-of-month + month: "الأول من ابريل", "الرابع من نيسان".

Foundation rules already cover relative days, weekdays, months, written dates
and HH:MM clock times. This file is a pure addition — it does not redefine
any rule from `rules.py`.

Cross-dimension dependencies are avoided so that callers passing `dims=("time",)`
to `parse()` still see these rules fire — the registry only loads rules from
the requested dimensions, so an `is_ordinal` predicate would silently fail when
the ordinal dimension is not part of `dims`. Ordinal day-of-month stems are
therefore matched directly via regex.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass

from puckling.dimensions.numeral.helpers import parse_arabic_int
from puckling.dimensions.time.ar._helpers import WrappedTimeData
from puckling.dimensions.time.grain import Grain
from puckling.dimensions.time.helpers import (
    at_day_of_month,
    at_month,
    intersect,
    pinned_instant,
    time,
)
from puckling.dimensions.time.types import TimeData
from puckling.types import RegexMatch, Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Resolve-time value classes


def _resolved_dict(value, context) -> dict | None:
    """Coerce a time-token value into its resolved dict via duck-typed `.resolve`."""
    resolver = getattr(value, "resolve", None)
    if not callable(resolver):
        return None
    out = resolver(context)
    if not isinstance(out, dict) or "value" not in out or "grain" not in out:
        return None
    return out


def _instant_part(d: dict) -> dict:
    """Reduce a resolved time dict to the `{value, grain}` payload of an instant."""
    return {"value": d["value"], "grain": d["grain"]}


class _SpanIdentityMixin:
    """Span-based equality for interval value objects.

    The base AR ruleset re-derives `WrappedTimeData` instances every iteration
    (TimeData wraps a fresh closure each firing), so values that are
    structurally equivalent compare unequal under default dataclass equality.
    Anchoring identity on the source span (plus the concrete subclass) collapses
    those equivalents to one parse-forest entry and prevents the engine from
    saturating exponentially.
    """

    __slots__ = ()

    def __eq__(self, other: object) -> bool:
        return (
            type(self) is type(other)
            and getattr(self, "span", None) == getattr(other, "span", None)
            and getattr(self, "grain", None) == getattr(other, "grain", None)
        )

    def __hash__(self) -> int:
        return hash((type(self).__name__, getattr(self, "span", None), getattr(self, "grain", None)))


@dataclass(frozen=True, slots=True, eq=False)
class IntervalCompound(_SpanIdentityMixin):
    """A closed interval built from two child time-token values."""

    left: object
    right: object
    grain: Grain
    span: tuple[tuple[int, int], tuple[int, int]]
    latent: bool = False

    def resolve(self, context) -> dict:
        a = _resolved_dict(self.left, context)
        b = _resolved_dict(self.right, context)
        if a is None or b is None:
            return {}
        return {
            "type": "interval",
            "from": _instant_part(a),
            "to": _instant_part(b),
        }


@dataclass(frozen=True, slots=True, eq=False)
class OpenIntervalBefore(_SpanIdentityMixin):
    """An interval bounded above by a single time value (e.g. "قبل/حتى X")."""

    bound: object
    grain: Grain
    span: tuple[int, int]
    latent: bool = False

    def resolve(self, context) -> dict:
        d = _resolved_dict(self.bound, context)
        if d is None:
            return {}
        return {"type": "interval", "to": _instant_part(d)}


@dataclass(frozen=True, slots=True, eq=False)
class OpenIntervalAfter(_SpanIdentityMixin):
    """An interval bounded below by a single time value (e.g. "بعد/منذ X")."""

    bound: object
    grain: Grain
    span: tuple[int, int]
    latent: bool = False

    def resolve(self, context) -> dict:
        d = _resolved_dict(self.bound, context)
        if d is None:
            return {}
        return {"type": "interval", "from": _instant_part(d)}


# ---------------------------------------------------------------------------
# Generic helpers


def _t(td: TimeData, *, key: tuple = ()) -> Token:
    return Token(dim="time", value=WrappedTimeData(inner=td, key=key))


def _v(value) -> Token:
    return Token(dim="time", value=value)


def _grain_of(t: Token) -> Grain | None:
    g = getattr(t.value, "grain", None)
    return g if isinstance(g, Grain) else None


def _is_instant_time(t: Token) -> bool:
    """Time tokens that do NOT already wrap an interval — used to anchor
    interval-building rules so they don't recursively consume their own output.

    Without this guard, "من X الى Y" produces an interval token that becomes
    eligible as `<X>` for another "من ... الى ..." rule, which combines with
    overlapping numeral/month tokens and saturates the engine in pathological
    ways for inputs containing numeric day-of-month plus a month name.
    """
    if t.dim != "time":
        return False
    return not isinstance(
        t.value, (IntervalCompound, OpenIntervalBefore, OpenIntervalAfter)
    )


def _finer_grain(a: Token, b: Token) -> Grain:
    """Pick the finer grain of two tokens, defaulting to DAY when unknown."""
    ga, gb = _grain_of(a), _grain_of(b)
    if ga is None and gb is None:
        return Grain.DAY
    if ga is None:
        return gb  # type: ignore[return-value]
    if gb is None:
        return ga
    return ga if ga.rank <= gb.rank else gb


# ---------------------------------------------------------------------------
# Interval productions


def _span(t: Token) -> tuple[int, int]:
    return (t.range.start, t.range.end)


def _prod_closed_interval(tokens: tuple[Token, ...]) -> Token | None:
    """Build a closed interval from `<connector> <X> <connector> <Y>`.

    Both `بين X و Y` and `من X (الى|حتى|...) Y` share this shape — the time
    operands sit at indices 1 and 3.
    """
    a, b = tokens[1], tokens[3]
    return _v(
        IntervalCompound(
            left=a.value,
            right=b.value,
            grain=_finer_grain(a, b),
            span=(_span(a), _span(b)),
        )
    )


def _prod_until(tokens: tuple[Token, ...]) -> Token | None:
    inner = tokens[1]
    grain = _grain_of(inner) or Grain.DAY
    return _v(OpenIntervalBefore(bound=inner.value, grain=grain, span=_span(inner)))


def _prod_after(tokens: tuple[Token, ...]) -> Token | None:
    inner = tokens[1]
    grain = _grain_of(inner) or Grain.DAY
    return _v(OpenIntervalAfter(bound=inner.value, grain=grain, span=_span(inner)))


# ---------------------------------------------------------------------------
# Numeric date forms.


def _captured(tokens: tuple[Token, ...], index: int) -> str | None:
    head = tokens[0]
    if not isinstance(head.value, RegexMatch):
        return None
    groups = head.value.groups
    if index >= len(groups):
        return None
    g = groups[index]
    return g if g is not None else None


def _prod_dd_mm(tokens: tuple[Token, ...]) -> Token | None:
    """DD/MM with the current reference year filled in."""
    dd = _captured(tokens, 0)
    mm = _captured(tokens, 1)
    if dd is None or mm is None:
        return None
    try:
        d, m = parse_arabic_int(dd), parse_arabic_int(mm)
    except ValueError:
        return None
    if not (1 <= d <= 31 and 1 <= m <= 12):
        return None
    # No year specified → leave the predicate to find the next matching day
    # within Duckling's 5-year scan window from the reference time.
    return _t(
        time(intersect(at_month(m), at_day_of_month(d)), Grain.DAY),
        key=("dd_mm", d, m),
    )


def _build_pinned_day(y: int, m: int, d: int) -> Token | None:
    try:
        moment = dt.datetime(y, m, d, tzinfo=dt.UTC)
    except ValueError:
        return None
    return _t(pinned_instant(moment, Grain.DAY), key=("pinned_day", y, m, d))


def _build_ymd_prod(
    *, dd_idx: int, mm_idx: int, yy_idx: int
) -> Callable[[tuple[Token, ...]], Token | None]:
    """Production factory for date forms with explicit year, parameterised by
    which capture group holds each component."""

    def go(tokens: tuple[Token, ...]) -> Token | None:
        dd = _captured(tokens, dd_idx)
        mm = _captured(tokens, mm_idx)
        yy = _captured(tokens, yy_idx)
        if dd is None or mm is None or yy is None:
            return None
        try:
            d, m, y = parse_arabic_int(dd), parse_arabic_int(mm), parse_arabic_int(yy)
        except ValueError:
            return None
        if not (1 <= d <= 31 and 1 <= m <= 12):
            return None
        if y < 100:
            # Two-digit year: treat as 20xx (mirrors Duckling's permissive parsing).
            y += 2000
        return _build_pinned_day(y, m, d)

    return go


_prod_dd_mm_yyyy = _build_ymd_prod(dd_idx=0, mm_idx=1, yy_idx=2)
_prod_yyyy_mm_dd = _build_ymd_prod(dd_idx=2, mm_idx=1, yy_idx=0)


# ---------------------------------------------------------------------------
# Ordinal-day-of-month + month: "الأول من ابريل", "الرابع من نيسان".
#
# We avoid an `is_ordinal` cross-dim predicate so this rule still fires when
# only the time dimension is loaded. Arabic ordinal stems are matched as part
# of the rule's leading regex.

# Stem → integer for ordinals 1..19 and feminine variants. We only need values
# that can plausibly be a day-of-month (1..31) here.
_ORDINAL_STEM_TO_INT: dict[str, int] = {
    "الاول": 1,
    "الأول": 1,
    "الأولى": 1,
    "الاولى": 1,
    "الحادي": 1,
    "الثاني": 2,
    "الثانية": 2,
    "الثان": 2,
    "الثالث": 3,
    "الثالثة": 3,
    "الرابع": 4,
    "الرابعة": 4,
    "الخامس": 5,
    "الخامسة": 5,
    "السادس": 6,
    "السادسة": 6,
    "السابع": 7,
    "السابعة": 7,
    "الثامن": 8,
    "الثامنة": 8,
    "التاسع": 9,
    "التاسعة": 9,
    "العاشر": 10,
    "العاشرة": 10,
}

# "Teen" stems: each is paired with "عشر" / "عشرة" → +10.
_ORDINAL_TEEN_TO_INT: dict[str, int] = {
    "الحادي": 11,
    "الإحدى": 11,
    "الاحدى": 11,
    "الحادية": 11,
    "الثاني": 12,
    "الثانية": 12,
    "الاثنى": 12,
    "الثان": 12,
    "الثالث": 13,
    "الثالثة": 13,
    "الرابع": 14,
    "الرابعة": 14,
    "الخامس": 15,
    "الخامسة": 15,
    "السادس": 16,
    "السادسة": 16,
    "السابع": 17,
    "السابعة": 17,
    "الثامن": 18,
    "الثامنة": 18,
    "التاسع": 19,
    "التاسعة": 19,
}

# Combined regex alternation for ordinal stems, longest first (so "الثالثة"
# binds before "الثالث" inside the regex engine).
_ORDINAL_RE = (
    r"(الأولى|الاولى|الإحدى|الاحدى|الحادية|الثانية|الثالثة|الرابعة|الخامسة|السادسة"
    r"|السابعة|الثامنة|التاسعة|العاشرة|الأول|الاول|الحادي|الثاني|الثان|الاثنى"
    r"|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر)"
)
_TEEN_SUFFIX = r"\s+عشرة?"


def _is_month_token(t: Token) -> bool:
    if t.dim != "time":
        return False
    inner = _unwrap(t.value)
    return isinstance(inner, TimeData) and inner.grain is Grain.MONTH


def _unwrap(value) -> TimeData | None:
    if isinstance(value, WrappedTimeData):
        return value.inner
    if isinstance(value, TimeData):
        return value
    return None


def _build_ordinal_dom_prod(
    table: dict[str, int],
) -> Callable[[tuple[Token, ...]], Token | None]:
    """Production factory: look up an ordinal stem in `table`, intersect with a
    trailing month token, and emit a day-grained `TimeData`."""

    def go(tokens: tuple[Token, ...]) -> Token | None:
        stem = _captured(tokens, 0)
        if stem is None:
            return None
        n = table.get(stem)
        if n is None:
            return None
        month_td = _unwrap(tokens[-1].value)
        if month_td is None:
            return None
        month_key = getattr(tokens[-1].value, "key", ()) or ("month_inner", id(month_td))
        return _t(
            time(intersect(month_td.predicate, at_day_of_month(n)), Grain.DAY),
            key=("ord_dom", n, month_key),
        )

    return go


_prod_ordinal_of_month = _build_ordinal_dom_prod(_ORDINAL_STEM_TO_INT)
_prod_ordinal_teen_of_month = _build_ordinal_dom_prod(_ORDINAL_TEEN_TO_INT)


# ---------------------------------------------------------------------------
# Rule list assembly.

_DD = r"(3[01]|[12][0-9]|0?[1-9]|[٠-٩]{1,2})"
_MM = r"(1[0-2]|0?[1-9]|[٠-٩]{1,2})"
_YY = r"([0-9٠-٩]{2,4})"
_YYYY = r"([0-9٠-٩]{4})"

# "إلى" / "الى" / "حتى" / "-" — closed-interval connector after "من".
_INTERVAL_CONNECT = r"(?:و\s?)?(?:\-|[إا]لى|حتى|لـ?)"

RULES: tuple[Rule, ...] = (
    # Closed intervals -------------------------------------------------------
    Rule(
        name="between <X> and <Y>",
        pattern=(
            regex(r"بين"),
            predicate(_is_instant_time, "is_instant_time"),
            regex(r"و"),
            predicate(_is_instant_time, "is_instant_time"),
        ),
        prod=_prod_closed_interval,
    ),
    Rule(
        name="from <X> to <Y>",
        pattern=(
            regex(r"من"),
            predicate(_is_instant_time, "is_instant_time"),
            regex(_INTERVAL_CONNECT),
            predicate(_is_instant_time, "is_instant_time"),
        ),
        prod=_prod_closed_interval,
    ),
    # Open intervals ---------------------------------------------------------
    Rule(
        name="until <X>",
        pattern=(
            regex(r"قبل|حتى|[إا]لى"),
            predicate(_is_instant_time, "is_instant_time"),
        ),
        prod=_prod_until,
    ),
    Rule(
        name="after <X>",
        pattern=(
            regex(r"بعد|منذ"),
            predicate(_is_instant_time, "is_instant_time"),
        ),
        prod=_prod_after,
    ),
    # Numeric date forms -----------------------------------------------------
    Rule(
        name="dd-mm-yyyy",
        pattern=(
            regex(_DD + r"\s?[/\-]\s?" + _MM + r"\s?[/\-]\s?" + _YY),
        ),
        prod=_prod_dd_mm_yyyy,
    ),
    Rule(
        name="yyyy-mm-dd",
        pattern=(
            regex(_YYYY + r"\-" + _MM + r"\-" + _DD),
        ),
        prod=_prod_yyyy_mm_dd,
    ),
    Rule(
        name="dd/mm",
        pattern=(regex(_DD + r"\s?[/\-]\s?" + _MM),),
        prod=_prod_dd_mm,
    ),
    # Ordinal day-of-month + month ------------------------------------------
    Rule(
        name="<ordinal-teen> عشر من <month>",
        pattern=(
            regex(_ORDINAL_RE + _TEEN_SUFFIX + r"\s+من(?:\s+شهر)?"),
            predicate(_is_month_token, "is_month_time"),
        ),
        prod=_prod_ordinal_teen_of_month,
    ),
    Rule(
        name="<ordinal-dom> من <month>",
        pattern=(
            regex(_ORDINAL_RE + r"\s+من(?:\s+شهر)?"),
            predicate(_is_month_token, "is_month_time"),
        ),
        prod=_prod_ordinal_of_month,
    ),
    # TODO(puckling): edge case — "بين الساعة 3 و الساعة 4 بعد العصر" with
    # absorbed "الساعة" / "بعد الظهر" markers (requires AM/PM modifier rules
    # not yet present in the AR base ruleset).
    # TODO(puckling): edge case — composite ordinal-dom intervals such as
    # "من الثالث والعشرون وحتى السادس والعشرين من شهر اكتوبر" (needs cross-rule
    # composition of two ordinal-dom partials sharing one month).
)
