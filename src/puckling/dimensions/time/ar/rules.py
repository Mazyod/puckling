"""Arabic time rules — port of `Duckling/Time/AR/Rules.hs`.

Coverage prioritises the highest-frequency Arabic date/time expressions: relative
days, day-of-week names, Gregorian + Levantine month names, HH:MM clock times,
the four-digit year, day-of-month + month, and the major Islamic holidays.

Less frequent or compositionally heavy upstream rules are deliberately omitted
and tagged below with `# TODO(puckling): edge case`.
"""

from __future__ import annotations

from puckling.dimensions.numeral.helpers import parse_arabic_int
from puckling.dimensions.time.ar._helpers import (
    HolidayValue,
    RelativeDayTime,
    RelativeGrainTime,
    TimeOfDayValue,
    WrappedTimeData,
    eid_al_adha,
    eid_al_fitr,
    muharram,
)
from puckling.dimensions.time.grain import Grain
from puckling.dimensions.time.helpers import (
    at_day_of_month,
    at_day_of_week,
    at_month,
    at_year,
    intersect,
    time,
)
from puckling.dimensions.time.types import TimeData
from puckling.types import Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Helpers internal to this module.

_WORD_BOUNDARY_LEFT = r"(?:(?<![\p{L}\p{N}_])|(?<=و))"
_WORD_BOUNDARY_RIGHT = r"(?![\p{L}\p{N}_])"
_NUMERIC_BOUNDARY_LEFT = r"(?<![\p{L}\p{N}_:/\-])"
_NUMERIC_BOUNDARY_RIGHT = r"(?![\p{L}\p{N}_:/\-])"
_CLOCK_BOUNDARY_LEFT = r"(?<![\p{L}\p{N}_:.])"
_CLOCK_BOUNDARY_RIGHT = r"(?![\p{L}\p{N}_])(?!(?:[:.][0-9٠-٩]))"


def _word_re(pattern: str) -> str:
    return rf"{_WORD_BOUNDARY_LEFT}(?:{pattern}){_WORD_BOUNDARY_RIGHT}"


def _numeric_re(pattern: str) -> str:
    return rf"{_NUMERIC_BOUNDARY_LEFT}(?:{pattern}){_NUMERIC_BOUNDARY_RIGHT}"


def _clock_re(pattern: str) -> str:
    return rf"{_CLOCK_BOUNDARY_LEFT}(?:{pattern}){_CLOCK_BOUNDARY_RIGHT}"


def _t(td: TimeData, *, key: tuple = ()) -> Token:
    """Wrap a foundation `TimeData` so `resolve()` produces the corpus-shaped dict.

    `key` is a stable semantic identifier; rules supply one so the engine can
    dedupe equivalent tokens despite TimeData's per-firing closure identity.
    """
    return Token(dim="time", value=WrappedTimeData(inner=td, key=key))


def _v(value) -> Token:
    return Token(dim="time", value=value)


def _day_of_week(weekday: int) -> TimeData:
    """Day-of-week with Duckling's `notImmediate` semantics — same-day → next week."""
    return TimeData(
        predicate=at_day_of_week(weekday),
        grain=Grain.DAY,
        not_immediate=True,
    )


# ---------------------------------------------------------------------------
# Reference-relative instants — driven by tables below.
#
# Upstream uses `cycleNth grain n`, which is reference-relative. We mirror it
# with `RelativeDayTime` / `RelativeGrainTime` rather than the foundation's
# predicate-based walk.


def _relative_day_rule(name: str, pattern: str, offset_days: int) -> Rule:
    def prod(_: tuple[Token, ...]) -> Token:
        return _v(RelativeDayTime(offset_days=offset_days))

    return Rule(name=name, pattern=(regex(_word_re(pattern)),), prod=prod)


def _relative_grain_rule(name: str, pattern: str, grain: Grain, offset: int) -> Rule:
    def prod(_: tuple[Token, ...]) -> Token:
        return _v(RelativeGrainTime(grain=grain, offset=offset))

    return Rule(name=name, pattern=(regex(_word_re(pattern)),), prod=prod)


_RELATIVE_DAYS: tuple[tuple[str, str, int], ...] = (
    ("today", r"اليوم", 0),
    ("tomorrow", r"(?:يوم )?(?:غدا?|الغد)|بكر[اةه]", 1),
    ("yesterday", r"[أا]مس|(?:ال|ام)بارح[ةه]?", -1),
    ("day after tomorrow", r"(?:يوم )?بعد (?:غدا?|الغد)", 2),
    ("day before yesterday", r"(?:يوم )?قبل [أا]مس", -2),
)

_RELATIVE_GRAINS: tuple[tuple[str, str, Grain, int], ...] = (
    ("now", r"الان|حالا|(?:في )?هذه اللحظ[ةه]", Grain.SECOND, 0),
    ("end of month", r"نهاي[ةه] الشهر", Grain.MONTH, 1),
    ("end of year", r"نهاي[ةه] (?:السن[ةه]|العام)", Grain.YEAR, 1),
    ("last week", r"الاسبوع الماضي", Grain.WEEK, -1),
    ("this week", r"(?:هذا )?الاسبوع", Grain.WEEK, 0),
    ("next week", r"الاسبوع (?:القادم|المقبل)", Grain.WEEK, 1),
    ("last month", r"الشهر الماضي", Grain.MONTH, -1),
    ("next month", r"الشهر (?:القادم|المقبل)", Grain.MONTH, 1),
    ("last year", r"(?:السنة|العام) الماضي[ةه]?", Grain.YEAR, -1),
    ("next year", r"(?:السنة|العام) (?:القادم[ةه]?|المقبل[ةه]?)", Grain.YEAR, 1),
)


# ---------------------------------------------------------------------------
# Day-of-week productions — generated from the table below.

_DAYS_OF_WEEK: tuple[tuple[str, str, int], ...] = (
    ("monday", r"(?:ال)?[اإ]ثنين", 0),
    ("tuesday", r"(?:ال)?ثلاثاء?", 1),
    ("wednesday", r"(?:ال)?[اأ]ربعاء?", 2),
    ("thursday", r"(?:ال)?خميس", 3),
    ("friday", r"(?:ال)?جمع[ةه]", 4),
    ("saturday", r"(?:ال)?سبت", 5),
    ("sunday", r"(?:ال)?[اأ]حد", 6),
)


def _make_dow_rule(name: str, pattern: str, weekday: int) -> Rule:
    def prod(_: tuple[Token, ...]) -> Token:
        return _t(_day_of_week(weekday), key=("dow", weekday))

    return Rule(name=f"day-of-week:{name}", pattern=(regex(_word_re(pattern)),), prod=prod)


# ---------------------------------------------------------------------------
# Months — Gregorian + Levantine names.

_MONTHS: tuple[tuple[str, str, int], ...] = (
    ("january", r"يناير|كانون(?: ال)?ثاني?", 1),
    ("february", r"فبراير|شباط", 2),
    ("march", r"مارس|[اآ]ذار", 3),
    ("april", r"[اأ]بريل|نيسان", 4),
    ("may", r"مايو|[اأ]ي[اآ]ر", 5),
    ("june", r"يونيو|حزيران", 6),
    ("july", r"يوليو|تموز", 7),
    ("august", r"[اأ]غسطس|[اآ]ب", 8),
    ("september", r"سي?بتمبر|[اأ]يلول", 9),
    ("october", r"[اأ]كتوبر|تشرين(?: ال)?[اأ]ول", 10),
    ("november", r"نوفمبر|تشرين(?: ال)?ثاني", 11),
    ("december", r"ديسمبر|كانون(?: ال)?[اأ]ول", 12),
)


def _make_month_rule(name: str, pattern: str, m: int) -> Rule:
    def prod(_: tuple[Token, ...]) -> Token:
        return _t(time(at_month(m), Grain.MONTH), key=("month", m))

    return Rule(name=f"month:{name}", pattern=(regex(_word_re(pattern)),), prod=prod)


# ---------------------------------------------------------------------------
# Day-of-month + month: "4 ابريل" or "4 من ابريل".


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


def _prod_dom_month(matched: tuple[Token, ...]) -> Token | None:
    day = _parse_first_int_group(matched)
    if day is None or not (1 <= day <= 31):
        return None
    month_td = _unwrap(matched[-1].value)
    if month_td is None:
        return None
    month_key = getattr(matched[-1].value, "key", ()) or ("month_inner", id(month_td))
    return _t(
        time(
            intersect(month_td.predicate, at_day_of_month(day)),
            Grain.DAY,
        ),
        key=("dom_month", day, month_key),
    )


# ---------------------------------------------------------------------------
# HH:MM patterns.


def _prod_hh_mm(matched: tuple[Token, ...]) -> Token | None:
    g = matched[0].value.groups
    if len(g) < 2 or g[0] is None or g[1] is None:
        return None
    hour = parse_arabic_int(g[0])
    minute = parse_arabic_int(g[1])
    # Dot-separated zero-hour clocks look like decimal amounts, e.g. 0.10.
    if hour == 0 and "." in matched[0].value.text:
        return None
    return _v(TimeOfDayValue(hour=hour, minute=minute))


# ---------------------------------------------------------------------------
# Four-digit year.


def _prod_year(matched: tuple[Token, ...]) -> Token:
    # Regex restricts to four ASCII digits in the 1000-2999 range.
    y = int(matched[0].value.text)
    return _t(time(at_year(y), Grain.YEAR), key=("year", y))


# ---------------------------------------------------------------------------
# Holidays — resolve forward from the reference time using the Hijri table.


def _prod_eid_al_fitr(_: tuple[Token, ...]) -> Token:
    return _v(HolidayValue(name="Eid al-Fitr", table=eid_al_fitr))


def _prod_eid_al_adha(_: tuple[Token, ...]) -> Token:
    return _v(HolidayValue(name="Eid al-Adha", table=eid_al_adha))


def _prod_islamic_new_year(_: tuple[Token, ...]) -> Token:
    return _v(HolidayValue(name="Islamic New Year", table=muharram))


# ---------------------------------------------------------------------------
# "في/بعد X أيام", "قبل X أيام" — relative day offsets.


def _parse_first_int_group(matched: tuple[Token, ...]) -> int | None:
    rx = matched[0]
    raw = next((g for g in rx.value.groups if g is not None), None)
    if raw is None:
        return None
    try:
        return parse_arabic_int(raw)
    except ValueError:
        return None


def _prod_in_days(matched: tuple[Token, ...]) -> Token | None:
    n = _parse_first_int_group(matched)
    return None if n is None else _v(RelativeDayTime(offset_days=n))


def _prod_days_ago(matched: tuple[Token, ...]) -> Token | None:
    n = _parse_first_int_group(matched)
    return None if n is None else _v(RelativeDayTime(offset_days=-n))


# ---------------------------------------------------------------------------
# Rule list assembly.

_DAY_RE = r"([0-9٠-٩]{1,2})"
_INT_RE = r"([0-9٠-٩]+)"

RULES: tuple[Rule, ...] = (
    # Reference-relative instants -------------------------------------------
    *(_relative_day_rule(n, p, off) for (n, p, off) in _RELATIVE_DAYS),
    *(_relative_grain_rule(n, p, g, off) for (n, p, g, off) in _RELATIVE_GRAINS),
    # Days of week -----------------------------------------------------------
    *(_make_dow_rule(n, p, wd) for (n, p, wd) in _DAYS_OF_WEEK),
    # Months -----------------------------------------------------------------
    *(_make_month_rule(n, p, m) for (n, p, m) in _MONTHS),
    # day of month + month ---------------------------------------------------
    Rule(
        name="<day-of-month> <month>",
        pattern=(
            regex(_DAY_RE),
            predicate(_is_month_token, "is_month_time"),
        ),
        prod=_prod_dom_month,
    ),
    Rule(
        name="<day-of-month> من <month>",
        pattern=(
            regex(_DAY_RE + r"\s+من"),
            predicate(_is_month_token, "is_month_time"),
        ),
        prod=_prod_dom_month,
    ),
    # HH:MM ------------------------------------------------------------------
    Rule(
        name="hh:mm",
        pattern=(
            regex(_clock_re(r"((?:[01]?[0-9])|(?:2[0-3]))[:.]([0-5][0-9])")),
        ),
        prod=_prod_hh_mm,
    ),
    # Year (4-digit) ---------------------------------------------------------
    Rule(name="year (4 digits)", pattern=(regex(_numeric_re(r"[12][0-9]{3}")),), prod=_prod_year),
    # In/Ago days ------------------------------------------------------------
    Rule(
        name="in <n> days",
        pattern=(
            regex(_word_re(rf"(?:في|بعد|خلال)\s+{_INT_RE}\s+(?:أيام|ايام|يوم|يوما?|يومين)")),
        ),
        prod=_prod_in_days,
    ),
    Rule(
        name="<n> days ago",
        pattern=(
            regex(_word_re(rf"قبل\s+{_INT_RE}\s+(?:أيام|ايام|يوم|يوما?|يومين)")),
        ),
        prod=_prod_days_ago,
    ),
    # Holidays ---------------------------------------------------------------
    Rule(name="Eid al-Fitr", pattern=(regex(_word_re(r"عيد ال[فق]طر")),), prod=_prod_eid_al_fitr),
    Rule(name="Eid al-Adha", pattern=(regex(_word_re(r"عيد ال[أا]ضحى")),), prod=_prod_eid_al_adha),
    Rule(
        name="Islamic New Year",
        pattern=(regex(_word_re(r"ر[أا]س السن[ةه] الهجري[ةه]")),),
        prod=_prod_islamic_new_year,
    ),
    # TODO(puckling): edge case — intervals (Ramadan period, "between X and Y").
    # TODO(puckling): edge case — quarter-/half-/third-past-hour, AM/PM.
    # TODO(puckling): edge case — ordinal-month-day, "first of march".
    # TODO(puckling): edge case — DD/MM and DD/MM/YYYY date forms.
)
