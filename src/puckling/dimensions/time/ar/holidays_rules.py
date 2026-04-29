"""Supplemental Arabic time rules — Christian/Islamic/national holidays,
parts-of-day, and relative-time expressions for week/month/year grains.

Coverage gap layered on top of `puckling.dimensions.time.ar.rules`. The main
file already handles Eid al-Fitr, Eid al-Adha, and Islamic New Year; this file
extends with:

  * Christian: Christmas (عيد الميلاد), Easter (عيد الفصح), Gregorian New Year
    (رأس السنة الميلادية).
  * Islamic (not yet covered): Mawlid (المولد النبوي), Isra and Mi'raj
    (الإسراء والمعراج), Day of Arafa (يوم عرفة), Ashura (عاشوراء), and Ramadan
    start (بداية رمضان).
  * National: Kuwait National Day (اليوم الوطني), Labour Day (عيد العمال).
  * Parts of day: morning (صباحا), evening (مساء), night (ليلا).
  * "بعد X" / "قبل X" generalised to weeks, months, years (the main file only
    handles days).
  * "كل اثنين" — recurring weekday; resolves to the next occurrence.

Hijri-anchored holidays use precomputed civil-observance tables (2010–2030);
outside that range the rule simply yields no match instead of guessing.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass

from puckling.dimensions.numeral.helpers import parse_arabic_int
from puckling.dimensions.time.ar._helpers import (
    HolidayValue,
    RelativeGrainTime,
    WrappedTimeData,
    eid_al_adha,
    eid_al_fitr,
    muharram,
)
from puckling.dimensions.time.computed import easter
from puckling.dimensions.time.grain import Grain
from puckling.dimensions.time.helpers import at_day_of_week
from puckling.dimensions.time.holiday_helpers import computed_holiday, fixed_holiday
from puckling.dimensions.time.types import (
    InstantValue,
    IntervalValue,
    TimeData,
    TimeValue,
)
from puckling.types import Rule, Token, regex

# Token wrapping helpers — duplicated from `rules.py` because the registry
# imports each `*_rules.py` independently and those helpers are private there.

_WORD_BOUNDARY_LEFT = r"(?:(?<![\p{L}\p{N}_])|(?<=و))"
_WORD_BOUNDARY_RIGHT = r"(?![\p{L}\p{N}_])"


def _word_re(pattern: str) -> str:
    return rf"{_WORD_BOUNDARY_LEFT}(?:{pattern}){_WORD_BOUNDARY_RIGHT}"


def _t(td: TimeData, *, key: tuple = ()) -> Token:
    return Token(dim="time", value=WrappedTimeData(inner=td, key=key))


def _v(value) -> Token:
    return Token(dim="time", value=value)


# ---------------------------------------------------------------------------
# Hijri tables for holidays not covered by the main file.
#
# Mawlid an-Nabi (12 Rabi' al-Awwal), Isra wa Mi'raj (27 Rajab) — civil
# observance dates. Outside 2010–2030 we return None (consistent with the main
# `_helpers.py` policy).

_MAWLID: dict[int, dt.date] = {
    2010: dt.date(2010, 2, 26),
    2011: dt.date(2011, 2, 15),
    2012: dt.date(2012, 2, 4),
    2013: dt.date(2013, 1, 24),
    2014: dt.date(2014, 1, 13),
    2015: dt.date(2015, 1, 3),
    2016: dt.date(2016, 12, 11),
    2017: dt.date(2017, 11, 30),
    2018: dt.date(2018, 11, 20),
    2019: dt.date(2019, 11, 9),
    2020: dt.date(2020, 10, 29),
    2021: dt.date(2021, 10, 18),
    2022: dt.date(2022, 10, 8),
    2023: dt.date(2023, 9, 27),
    2024: dt.date(2024, 9, 15),
    2025: dt.date(2025, 9, 4),
    2026: dt.date(2026, 8, 25),
    2027: dt.date(2027, 8, 14),
    2028: dt.date(2028, 8, 3),
    2029: dt.date(2029, 7, 24),
    2030: dt.date(2030, 7, 13),
}

_ISRA_MIRAJ: dict[int, dt.date] = {
    2010: dt.date(2010, 7, 9),
    2011: dt.date(2011, 6, 29),
    2012: dt.date(2012, 6, 17),
    2013: dt.date(2013, 6, 6),
    2014: dt.date(2014, 5, 26),
    2015: dt.date(2015, 5, 16),
    2016: dt.date(2016, 5, 5),
    2017: dt.date(2017, 4, 24),
    2018: dt.date(2018, 4, 13),
    2019: dt.date(2019, 4, 3),
    2020: dt.date(2020, 3, 22),
    2021: dt.date(2021, 3, 11),
    2022: dt.date(2022, 2, 28),
    2023: dt.date(2023, 2, 18),
    2024: dt.date(2024, 2, 8),
    2025: dt.date(2025, 1, 27),
    2026: dt.date(2026, 1, 16),
    2027: dt.date(2027, 1, 5),
    2028: dt.date(2028, 12, 14),
    2029: dt.date(2029, 12, 3),
    2030: dt.date(2030, 11, 23),
}


def _mawlid(year: int) -> dt.date | None:
    return _MAWLID.get(year)


def _isra_miraj(year: int) -> dt.date | None:
    return _ISRA_MIRAJ.get(year)


def _day_of_arafa(year: int) -> dt.date | None:
    """9 Dhul-Hijjah — the eve of Eid al-Adha."""
    base = eid_al_adha(year)
    return None if base is None else base - dt.timedelta(days=1)


def _ashura(year: int) -> dt.date | None:
    """10 Muharram — nine days after the Islamic New Year."""
    base = muharram(year)
    return None if base is None else base + dt.timedelta(days=9)


def _ramadan_start(year: int) -> dt.date | None:
    """1 Ramadan — observed roughly 30 days before Eid al-Fitr.

    The lunar month is 29 or 30 days; using a fixed 30-day offset matches
    civil-calendar publications closely enough for the 2010–2030 table.
    """
    # TODO(puckling): edge case — exact 1 Ramadan dates vary by 1 day in some
    # years vs Eid_al_Fitr - 30. Replace with a dedicated table if precision
    # ever matters.
    base = eid_al_fitr(year)
    return None if base is None else base - dt.timedelta(days=30)


# ---------------------------------------------------------------------------
# Parts-of-day — interval values anchored to the reference date.
#
# Mirrors the EN rule pattern: a custom value class so `resolve()` returns the
# IntervalValue dict directly. Marked `latent=True` so callers must opt in via
# `Options(with_latent=True)` to surface them (matches Duckling semantics).


@dataclass(frozen=True, slots=True)
class PartOfDayInterval:
    """A part-of-day named interval (e.g. morning = 04:00–12:00 today)."""

    name: str
    start_hour: int
    end_hour: int
    grain: Grain = Grain.HOUR
    latent: bool = True

    def resolve(self, context) -> TimeValue:
        ref_day = context.reference_time.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start = InstantValue(
            value=ref_day.replace(hour=self.start_hour), grain=Grain.HOUR
        )
        if self.end_hour == 0:
            end_value = ref_day + dt.timedelta(days=1)
        elif self.end_hour <= self.start_hour:
            end_value = ref_day + dt.timedelta(days=1, hours=self.end_hour)
        else:
            end_value = ref_day.replace(hour=self.end_hour)
        end = InstantValue(value=end_value, grain=Grain.HOUR)
        return TimeValue(primary=IntervalValue(start=start, end=end))


def _part_of_day_rule(name: str, pattern: str, start_h: int, end_h: int) -> Rule:
    def prod(_: tuple[Token, ...]) -> Token:
        return _v(PartOfDayInterval(name=name, start_hour=start_h, end_hour=end_h))

    return Rule(name=f"part-of-day:{name}", pattern=(regex(_word_re(pattern)),), prod=prod)


# ---------------------------------------------------------------------------
# Holiday rule builders.


def _fixed_holiday_rule(name: str, pattern: str, month: int, day: int) -> Rule:
    def prod(_: tuple[Token, ...]) -> Token:
        return _t(fixed_holiday(month, day, name), key=("fixed_holiday", name, month, day))

    return Rule(name=f"holiday:{name}", pattern=(regex(_word_re(pattern)),), prod=prod)


def _hijri_holiday_rule(
    name: str, pattern: str, table: Callable[[int], dt.date | None]
) -> Rule:
    def prod(_: tuple[Token, ...]) -> Token:
        return _v(HolidayValue(name=name, table=table))

    return Rule(name=f"holiday:{name}", pattern=(regex(_word_re(pattern)),), prod=prod)


def _easter_holiday_rule(name: str, pattern: str) -> Rule:
    """Easter Sunday — uses the year-keyed `easter` computation as a TimeData
    predicate (resolver walks forward to the next matching day)."""

    def prod(_: tuple[Token, ...]) -> Token:
        return _t(computed_holiday(name, easter), key=("computed_holiday", name))

    return Rule(name=f"holiday:{name}", pattern=(regex(_word_re(pattern)),), prod=prod)


# ---------------------------------------------------------------------------
# "بعد/في/خلال X اسابيع|شهور|سنوات" — relative offsets at week/month/year grain.

_INT_RE = r"([0-9٠-٩]+)"

# Singular and broken-plural noun forms (أسبوع → أسابيع, شهر → شهور/أشهر,
# سنة → سنوات, عام → أعوام) for use after an explicit numeral. Dual forms
# (اسبوعين, شهرين, سنتين, عامين) embed their own count — see `_DUAL_GRAIN_UNIT`.
_GRAIN_UNIT: tuple[tuple[str, str, Grain], ...] = (
    ("week", r"(?:[أا]سبوعا?|[أا]سابيع)", Grain.WEEK),
    ("month", r"(?:شهرا?|شهور|[أا]شهر)", Grain.MONTH),
    ("year", r"(?:سن[ةه]|سنوات|سنين|عام|[أا]عوام)", Grain.YEAR),
)


def _parse_first_int_group(matched: tuple[Token, ...]) -> int | None:
    rx = matched[0]
    raw = next((g for g in rx.value.groups if g is not None), None)
    if raw is None:
        return None
    try:
        return parse_arabic_int(raw)
    except ValueError:
        return None


def _make_in_grain_rule(name: str, unit: str, grain: Grain) -> Rule:
    pat = rf"(?:في|بعد|خلال)\s+{_INT_RE}\s+{unit}"

    def prod(matched: tuple[Token, ...]) -> Token | None:
        n = _parse_first_int_group(matched)
        return None if n is None else _v(RelativeGrainTime(grain=grain, offset=n))

    return Rule(name=f"in <n> {name}s", pattern=(regex(_word_re(pat)),), prod=prod)


def _make_ago_grain_rule(name: str, unit: str, grain: Grain) -> Rule:
    pat = rf"قبل\s+{_INT_RE}\s+{unit}"

    def prod(matched: tuple[Token, ...]) -> Token | None:
        n = _parse_first_int_group(matched)
        return None if n is None else _v(RelativeGrainTime(grain=grain, offset=-n))

    return Rule(name=f"<n> {name}s ago", pattern=(regex(_word_re(pat)),), prod=prod)


# Arabic dual nouns embed an implicit "2" (e.g. اسبوعين = "two weeks"); they
# don't carry a numeral the previous rules can latch onto, so we emit dedicated
# patterns with a hard-coded offset of ±2.
_DUAL_GRAIN_UNIT: tuple[tuple[str, str, Grain], ...] = (
    ("week", r"[أا]سبوعين", Grain.WEEK),
    ("month", r"شهرين", Grain.MONTH),
    ("year", r"(?:سنتين|عامين)", Grain.YEAR),
)


def _make_in_dual_rule(name: str, unit: str, grain: Grain) -> Rule:
    pat = rf"(?:في|بعد|خلال)\s+{unit}"

    def prod(_: tuple[Token, ...]) -> Token:
        return _v(RelativeGrainTime(grain=grain, offset=2))

    return Rule(name=f"in two {name}s (dual)", pattern=(regex(_word_re(pat)),), prod=prod)


def _make_ago_dual_rule(name: str, unit: str, grain: Grain) -> Rule:
    pat = rf"قبل\s+{unit}"

    def prod(_: tuple[Token, ...]) -> Token:
        return _v(RelativeGrainTime(grain=grain, offset=-2))

    return Rule(name=f"two {name}s ago (dual)", pattern=(regex(_word_re(pat)),), prod=prod)


# ---------------------------------------------------------------------------
# "كل اثنين" — every <day-of-week>.

_DAYS_OF_WEEK: tuple[tuple[str, str, int], ...] = (
    ("monday", r"(?:ال)?[اإ]ثنين", 0),
    ("tuesday", r"(?:ال)?ثلاثاء?", 1),
    ("wednesday", r"(?:ال)?[اأ]ربعاء?", 2),
    ("thursday", r"(?:ال)?خميس", 3),
    ("friday", r"(?:ال)?جمع[ةه]", 4),
    ("saturday", r"(?:ال)?سبت", 5),
    ("sunday", r"(?:ال)?[اأ]حد", 6),
)


def _every_dow_rule(name: str, dow_pattern: str, weekday: int) -> Rule:
    """`كل <weekday>` — Duckling resolves recurring weekday to the next
    occurrence (same shape as `الاثنين`).
    """
    pat = rf"كل\s+{dow_pattern}"

    def prod(_: tuple[Token, ...]) -> Token:
        return _t(
            TimeData(
                predicate=at_day_of_week(weekday),
                grain=Grain.DAY,
                not_immediate=True,
            ),
            key=("every_dow", weekday),
        )

    return Rule(name=f"every {name}", pattern=(regex(_word_re(pat)),), prod=prod)


# ---------------------------------------------------------------------------
# Rule list assembly.


RULES: tuple[Rule, ...] = (
    # ----- Christian holidays --------------------------------------------
    _fixed_holiday_rule(
        "Christmas",
        r"عيد الميلاد(?:\s+المجيد)?|(?:يوم |عطل[ةه] )?(?:ال)?كري?سماس",
        12,
        25,
    ),
    _easter_holiday_rule("Easter Sunday", r"عيد (?:ال)?فصح"),
    # `رأس السنة الميلادية` — Gregorian Jan 1, distinct from the existing
    # Hijri-anchored "Islamic New Year" rule in the main file.
    _fixed_holiday_rule(
        "New Year's Day",
        r"ر[أا]س السن[ةه](?: الميلادي[ةه]|(?!\s+[\p{L}]))",
        1,
        1,
    ),
    # ----- Islamic holidays (not yet covered) ----------------------------
    _hijri_holiday_rule(
        "Mawlid",
        r"(?:عيد )?المولد(?: النبوي(?: الشريف)?|(?!\s+[\p{L}]))",
        _mawlid,
    ),
    _hijri_holiday_rule(
        "Isra and Mi'raj",
        r"(?:ذكرى )?(?:ال)?[إا]سراء و(?:ال)?معراج",
        _isra_miraj,
    ),
    _hijri_holiday_rule("Day of Arafa", r"يوم عرف[ةه]|وقف[ةه] عرف[ةه]", _day_of_arafa),
    _hijri_holiday_rule("Ashura", r"عاشوراء|يوم عاشوراء", _ashura),
    _hijri_holiday_rule(
        "Ramadan",
        r"بداي[ةه] (?:شهر )?رمضان|[أا]ول رمضان|غر[ةه] رمضان",
        _ramadan_start,
    ),
    # ----- National holidays ---------------------------------------------
    # Kuwait National Day (Feb 25) — the most relevant default in this
    # codebase's deployment context.
    # TODO(puckling): edge case — Saudi (Sep 23) / UAE (Dec 2) etc. all share
    # the phrase "اليوم الوطني"; the Kuwaiti default wins here. A future
    # `Region`-aware dispatch could pick the right month/day per locale.
    _fixed_holiday_rule(
        "National Day",
        r"اليوم الوطني|العيد الوطني",
        2,
        25,
    ),
    _fixed_holiday_rule(
        "Labour Day",
        r"عيد العمال|يوم العمال|عيد العم(?:ل|الي?)",
        5,
        1,
    ),
    # ----- Parts of day (latent intervals) -------------------------------
    _part_of_day_rule("morning", r"صباحاً?|الصباح", 4, 12),
    _part_of_day_rule("evening", r"مساءا?ً?|المساء|عصرا?ً?", 18, 0),
    _part_of_day_rule("night", r"ليلا?ً?|الليل[ةه]?", 18, 0),
    # ----- "بعد/في/خلال X <grain>" / "قبل X <grain>" ---------------------
    *(_make_in_grain_rule(n, u, g) for (n, u, g) in _GRAIN_UNIT),
    *(_make_ago_grain_rule(n, u, g) for (n, u, g) in _GRAIN_UNIT),
    # Dual-noun forms ("two weeks", etc.) need their own rules — the noun
    # itself encodes the count, so there's no numeral to capture.
    *(_make_in_dual_rule(n, u, g) for (n, u, g) in _DUAL_GRAIN_UNIT),
    *(_make_ago_dual_rule(n, u, g) for (n, u, g) in _DUAL_GRAIN_UNIT),
    # ----- "كل <weekday>" -------------------------------------------------
    *(_every_dow_rule(n, p, wd) for (n, p, wd) in _DAYS_OF_WEEK),
    # TODO(puckling): edge case — "كل يوم|أسبوع|شهر|سنة" recurring period
    # frames; would need a periodic-time value distinct from a single instant.
)
