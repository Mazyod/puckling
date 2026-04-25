"""Arabic time — supplemental rules for intervals, DD/MM dates, ordinal-DOM.

Augments the base AR Time ruleset with:
- Closed intervals: "بين X و Y", "من X إلى Y", "من X حتى Y", "X - Y", "X إلى Y".
- Open intervals: "قبل X" / "حتى X" (before), "بعد X" / "منذ X" (after).
- Numeric date forms: "DD/MM", "DD-MM-YYYY", "DD/MM/YYYY", "YYYY-MM-DD".
- Ordinal day-of-month + month: "الأول من ابريل", "الرابع من نيسان".

Foundation rules already cover relative days, weekdays, months, written dates
and HH:MM clock times. This file is a pure addition — it does not redefine
any rule from `rules.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from puckling.dimensions.numeral.helpers import parse_arabic_int
from puckling.dimensions.ordinal.types import OrdinalValue
from puckling.dimensions.time.ar._helpers import WrappedTimeData
from puckling.dimensions.time.grain import Grain
from puckling.dimensions.time.helpers import (
    at_day_of_month,
    at_month,
    at_year,
    intersect,
    time,
)
from puckling.dimensions.time.types import TimeData
from puckling.predicates import is_ordinal, is_time
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


@dataclass(frozen=True, slots=True)
class IntervalCompound:
    """A closed interval built from two child time-token values."""

    left: object
    right: object
    grain: Grain
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


@dataclass(frozen=True, slots=True)
class OpenIntervalBefore:
    """An interval bounded above by a single time value (e.g. "قبل/حتى X")."""

    bound: object
    grain: Grain
    latent: bool = False

    def resolve(self, context) -> dict:
        d = _resolved_dict(self.bound, context)
        if d is None:
            return {}
        return {"type": "interval", "to": _instant_part(d)}


@dataclass(frozen=True, slots=True)
class OpenIntervalAfter:
    """An interval bounded below by a single time value (e.g. "بعد/منذ X")."""

    bound: object
    grain: Grain
    latent: bool = False

    def resolve(self, context) -> dict:
        d = _resolved_dict(self.bound, context)
        if d is None:
            return {}
        return {"type": "interval", "from": _instant_part(d)}


# ---------------------------------------------------------------------------
# Helpers


def _t(td: TimeData) -> Token:
    return Token(dim="time", value=WrappedTimeData(inner=td))


def _v(value) -> Token:
    return Token(dim="time", value=value)


def _grain_of(t: Token) -> Grain | None:
    g = getattr(t.value, "grain", None)
    return g if isinstance(g, Grain) else None


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


def _prod_between_and(tokens: tuple[Token, ...]) -> Token | None:
    a, b = tokens[1], tokens[3]
    return _v(IntervalCompound(left=a.value, right=b.value, grain=_finer_grain(a, b)))


def _prod_from_to(tokens: tuple[Token, ...]) -> Token | None:
    a, b = tokens[1], tokens[3]
    return _v(IntervalCompound(left=a.value, right=b.value, grain=_finer_grain(a, b)))


def _prod_dash(tokens: tuple[Token, ...]) -> Token | None:
    a, b = tokens[0], tokens[2]
    return _v(IntervalCompound(left=a.value, right=b.value, grain=_finer_grain(a, b)))


def _prod_until(tokens: tuple[Token, ...]) -> Token | None:
    inner = tokens[1]
    grain = _grain_of(inner) or Grain.DAY
    return _v(OpenIntervalBefore(bound=inner.value, grain=grain))


def _prod_after(tokens: tuple[Token, ...]) -> Token | None:
    inner = tokens[1]
    grain = _grain_of(inner) or Grain.DAY
    return _v(OpenIntervalAfter(bound=inner.value, grain=grain))


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
    return _t(time(intersect(at_month(m), at_day_of_month(d)), Grain.DAY))


def _prod_dd_mm_yyyy(tokens: tuple[Token, ...]) -> Token | None:
    dd = _captured(tokens, 0)
    mm = _captured(tokens, 1)
    yy = _captured(tokens, 2)
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
    return _t(
        time(
            intersect(at_year(y), at_month(m), at_day_of_month(d)),
            Grain.DAY,
        )
    )


def _prod_yyyy_mm_dd(tokens: tuple[Token, ...]) -> Token | None:
    yy = _captured(tokens, 0)
    mm = _captured(tokens, 1)
    dd = _captured(tokens, 2)
    if yy is None or mm is None or dd is None:
        return None
    try:
        y, m, d = parse_arabic_int(yy), parse_arabic_int(mm), parse_arabic_int(dd)
    except ValueError:
        return None
    if not (1 <= d <= 31 and 1 <= m <= 12):
        return None
    if y < 100:
        y += 2000
    return _t(
        time(
            intersect(at_year(y), at_month(m), at_day_of_month(d)),
            Grain.DAY,
        )
    )


# ---------------------------------------------------------------------------
# Ordinal-day-of-month + month: "الأول من ابريل", "الرابع من نيسان".


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


def _ordinal_int(t: Token) -> int | None:
    if t.dim != "ordinal":
        return None
    val = t.value
    if not isinstance(val, OrdinalValue):
        return None
    return val.value if 1 <= val.value <= 31 else None


def _prod_ordinal_of_month(tokens: tuple[Token, ...]) -> Token | None:
    # tokens: <ordinal> <regex "من"> <month-time>
    day = _ordinal_int(tokens[0])
    month_td = _unwrap(tokens[-1].value)
    if day is None or month_td is None:
        return None
    return _t(time(intersect(month_td.predicate, at_day_of_month(day)), Grain.DAY))


def _prod_ordinal_day_of_month(tokens: tuple[Token, ...]) -> Token | None:
    # "اليوم الأول من ابريل" — "اليوم" + ordinal + "من" + month.
    day = _ordinal_int(tokens[1])
    month_td = _unwrap(tokens[-1].value)
    if day is None or month_td is None:
        return None
    return _t(time(intersect(month_td.predicate, at_day_of_month(day)), Grain.DAY))


# ---------------------------------------------------------------------------
# Rule list assembly.

_DD = r"(3[01]|[12][0-9]|0?[1-9]|[٠-٩]{1,2})"
_MM = r"(1[0-2]|0?[1-9]|[٠-٩]{1,2})"
_YY = r"([0-9٠-٩]{2,4})"
_YYYY = r"([0-9٠-٩]{4})"

# "إلى" / "الى" / "حتى" / "-" — closed-interval connector.
_INTERVAL_CONNECT = r"(?:و\s?)?(?:\-|[إا]لى|حتى|لـ?)"
_INTERVAL_TO = r"[إا]لى|حتى"

RULES: tuple[Rule, ...] = (
    # Closed intervals -------------------------------------------------------
    Rule(
        name="between <X> and <Y>",
        pattern=(
            regex(r"بين"),
            predicate(is_time, "is_time"),
            regex(r"و"),
            predicate(is_time, "is_time"),
        ),
        prod=_prod_between_and,
    ),
    Rule(
        name="from <X> to <Y>",
        pattern=(
            regex(r"من"),
            predicate(is_time, "is_time"),
            regex(_INTERVAL_CONNECT),
            predicate(is_time, "is_time"),
        ),
        prod=_prod_from_to,
    ),
    Rule(
        name="<X> to <Y> (dash / إلى / حتى)",
        pattern=(
            predicate(is_time, "is_time"),
            regex(r"\-|" + _INTERVAL_TO),
            predicate(is_time, "is_time"),
        ),
        prod=_prod_dash,
    ),
    # Open intervals ---------------------------------------------------------
    Rule(
        name="until <X>",
        pattern=(regex(r"قبل|حتى|[إا]لى"), predicate(is_time, "is_time")),
        prod=_prod_until,
    ),
    Rule(
        name="after <X>",
        pattern=(regex(r"بعد|منذ"), predicate(is_time, "is_time")),
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
        name="<ordinal-dom> من <month>",
        pattern=(
            predicate(is_ordinal, "is_ordinal"),
            regex(r"من(?:\s+شهر)?"),
            predicate(_is_month_token, "is_month_time"),
        ),
        prod=_prod_ordinal_of_month,
    ),
    Rule(
        name="اليوم <ordinal-dom> من <month>",
        pattern=(
            regex(r"اليوم"),
            predicate(is_ordinal, "is_ordinal"),
            regex(r"من(?:\s+شهر)?"),
            predicate(_is_month_token, "is_month_time"),
        ),
        prod=_prod_ordinal_day_of_month,
    ),
    # TODO(puckling): edge case — "بين الساعة 3 و الساعة 4 بعد العصر" with
    # absorbed "الساعة" / "بعد الظهر" markers (requires AM/PM modifier rules
    # not yet present in the AR base ruleset).
    # TODO(puckling): edge case — composite ordinal-dom intervals such as
    # "من الثالث والعشرون وحتى السادس والعشرين من شهر اكتوبر" (needs cross-rule
    # composition of two ordinal-dom partials sharing one month).
)
