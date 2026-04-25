"""Time value types — `TimeData`, `TimeValue`, `Form`, `IntervalDirection`."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from puckling.dimensions.time.grain import Grain


class IntervalDirection(Enum):
    BEFORE = "before"
    AFTER = "after"


class IntervalType(Enum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class TimeOfDay:
    hours: int | None
    is_12h: bool


@dataclass(frozen=True, slots=True)
class MonthForm:
    month: int


@dataclass(frozen=True, slots=True)
class DayOfWeekForm:
    pass


@dataclass(frozen=True, slots=True)
class PartOfDayForm:
    pass


Form = TimeOfDay | MonthForm | DayOfWeekForm | PartOfDayForm

# A predicate over `dt.datetime` that resolves to True iff that instant is part
# of the time value. Used by the resolver to find the next/previous matching
# instant relative to a reference time. Productions build these compositionally
# (see `helpers.py`).
TimePredicate = Callable[[dt.datetime], bool]


@dataclass(frozen=True, slots=True)
class InstantValue:
    """A specific moment, anchored to a particular grain."""

    value: dt.datetime
    grain: Grain

    def to_dict(self) -> dict:
        return {
            "value": self.value.isoformat(),
            "grain": self.grain.value,
        }


@dataclass(frozen=True, slots=True)
class IntervalValue:
    """A closed-open interval between two instants."""

    start: InstantValue
    end: InstantValue

    def to_dict(self) -> dict:
        return {
            "type": "interval",
            "from": self.start.to_dict(),
            "to": self.end.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class OpenIntervalValue:
    """An interval bounded on one side."""

    instant: InstantValue
    direction: IntervalDirection

    def to_dict(self) -> dict:
        key = "to" if self.direction is IntervalDirection.BEFORE else "from"
        return {"type": "interval", key: self.instant.to_dict()}


SingleTimeValue = InstantValue | IntervalValue | OpenIntervalValue


@dataclass(frozen=True, slots=True)
class TimeValue:
    """The resolved value surfaced by `resolve()`."""

    primary: SingleTimeValue
    alternates: tuple[SingleTimeValue, ...] = ()
    holiday: str | None = None

    def start_datetime(self) -> dt.datetime | None:
        """The lower bound of `primary`, or `None` if the value is upper-bounded only.

        Saves callers the isinstance ladder over `InstantValue | IntervalValue
        | OpenIntervalValue`. An instant is its own start; a closed interval
        returns its `start.value`; an open `BEFORE` interval has no start.
        """
        match self.primary:
            case InstantValue():
                return self.primary.value
            case IntervalValue():
                return self.primary.start.value
            case OpenIntervalValue(direction=IntervalDirection.AFTER):
                return self.primary.instant.value
            case OpenIntervalValue():
                return None

    def end_datetime(self) -> dt.datetime | None:
        """The upper bound of `primary`, or `None` if the value is lower-bounded only.

        Instants intentionally return `None` (an instant has a value, not an
        end); use `start_datetime()` and the instant's `grain` if you need a
        grain-bounded range.
        """
        match self.primary:
            case InstantValue():
                return None
            case IntervalValue():
                return self.primary.end.value
            case OpenIntervalValue(direction=IntervalDirection.BEFORE):
                return self.primary.instant.value
            case OpenIntervalValue():
                return None

    def to_dict(self) -> dict:
        out: dict = {"type": "value", **self.primary.to_dict()}
        if isinstance(self.primary, IntervalValue) and "from" in out:
            out.pop("value", None)
            out.pop("grain", None)
        if self.alternates:
            out["values"] = [a.to_dict() for a in self.alternates]
        if self.holiday is not None:
            out["holiday"] = self.holiday
        return out


@dataclass(frozen=True, slots=True)
class TimeData:
    """The pre-resolution time value carried by tokens.

    `predicate` picks instants that satisfy this time expression. The resolver
    walks forward/backward from the reference time to find the next match.
    """

    predicate: TimePredicate
    grain: Grain
    latent: bool = False
    not_immediate: bool = False
    form: Form | None = None
    direction: IntervalDirection | None = None
    holiday: str | None = None
    has_timezone: bool = False
    # When set, the resolver will use this value directly instead of searching.
    pinned: SingleTimeValue | None = None

    def resolve(self, context) -> TimeValue | None:
        from puckling.dimensions.time.helpers import resolve_time_data

        value = resolve_time_data(self, context.reference_time)
        if value is None:
            return None
        return TimeValue(primary=value, holiday=self.holiday)
