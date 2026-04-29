"""Arabic clock-time rules — supplements `time/ar/rules.py`.

Foundation `time/ar/rules.py` already covers `hh:mm` digit pairs; this module
fills the gaps for spoken/written clock expressions:

- "الساعة 5" / "الساعة الخامسة"     — o'clock (numeric or word hour)
- "5 صباحا" / "5 مساء" / "5 ظهرا"   — AM / PM / afternoon modifiers
- "5 و نصف" / "5 و ربع" / "5 الا ربع" — half/quarter past, quarter to
- "ظهرا" / "منتصف النهار" / "منتصف الليل" — noon / midnight

Tokens are emitted as `TimeOfDayValue` (defined in `_helpers.py`) which already
anchors a wall-clock time to the reference date.
"""

from __future__ import annotations

from dataclasses import replace

from puckling.dimensions.numeral.helpers import parse_arabic_int
from puckling.dimensions.time.ar._helpers import TimeOfDayValue
from puckling.dimensions.time.grain import Grain
from puckling.types import RegexMatch, Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Token helpers

_WORD_BOUNDARY_LEFT = r"(?:(?<![\p{L}\p{N}_])|(?<=و))"
_WORD_BOUNDARY_RIGHT = r"(?![\p{L}\p{N}_])"
_NUMERIC_BOUNDARY_LEFT = r"(?<![\p{L}\p{N}_])"
_NUMERIC_BOUNDARY_RIGHT = r"(?![\p{L}\p{N}_])"
_VALID_MINUTE_RE = r"(?:[0-5]?[0-9]|[٠-٥]?[٠-٩])"
_VALID_AND_CONTINUATION_RE = (
    rf"(?:\s*نصف(?:\s+ساع[ةه])?|\s*ربع(?:\s+ساع[ةه])?"
    rf"|\s*{_VALID_MINUTE_RE}\s+(?:دقيق[ةه]|دقائق)){_WORD_BOUNDARY_RIGHT}"
)
_VALID_QUARTER_TO_RE = rf"\s+ربعا?{_WORD_BOUNDARY_RIGHT}"
_CLOCK_CONTINUATION_GUARD = (
    rf"(?!\s+و(?!{_VALID_AND_CONTINUATION_RE}))"
    rf"(?!\s+[إا]لا(?!{_VALID_QUARTER_TO_RE}))"
)


def _word_re(pattern: str) -> str:
    return rf"{_WORD_BOUNDARY_LEFT}(?:{pattern}){_WORD_BOUNDARY_RIGHT}"


def _numeric_re(pattern: str) -> str:
    return rf"{_NUMERIC_BOUNDARY_LEFT}(?:{pattern}){_NUMERIC_BOUNDARY_RIGHT}"


def _clock_head_re(pattern: str) -> str:
    return _word_re(pattern) + _CLOCK_CONTINUATION_GUARD


def _v(value: TimeOfDayValue) -> Token:
    return Token(dim="time", value=value)


def _is_clock(t: Token) -> bool:
    return t.dim == "time" and isinstance(t.value, TimeOfDayValue)


def _regex_match(t: Token) -> RegexMatch | None:
    return t.value if isinstance(t.value, RegexMatch) else None


# ---------------------------------------------------------------------------
# Word-form hours: الواحدة, الثانية, ..., الثانية عشرة (1..12)
#
# Listed with optional ال prefix; resolution is grain=hour, latent until paired
# with an explicit "الساعة" or an AM/PM suffix.

_WORD_HOURS: tuple[tuple[str, int], ...] = (
    (r"(?:ال)?واحد[ةه]", 1),
    # "ثاني[ةه]" alone is 2; "ثاني[ةه] عشر[ةه]" promotes to 12 (handled in prod).
    (r"(?:ال)?ثاني[ةه](?:\s+عشر[ةه])?", 2),
    (r"(?:ال)?ثالث[ةه]", 3),
    (r"(?:ال)?رابع[ةه]", 4),
    (r"(?:ال)?خامس[ةه]", 5),
    (r"(?:ال)?سادس[ةه]", 6),
    (r"(?:ال)?سابع[ةه]", 7),
    (r"(?:ال)?ثامن[ةه]", 8),
    (r"(?:ال)?تاسع[ةه]", 9),
    (r"(?:ال)?عاشر[ةه]", 10),
    (r"(?:ال)?حادي[ةه]\s+عشر[ةه]", 11),
)


def _make_word_hour_rule(pat: str, base_hour: int) -> Rule:
    def prod(matched: tuple[Token, ...]) -> Token | None:
        rm = _regex_match(matched[0])
        if rm is None:
            return None
        # "الثانية عشرة" promotes the base 2 → 12.
        h = 12 if base_hour == 2 and "عشر" in rm.text else base_hour
        # Latent: a bare ordinal hour without "الساعة" or AM/PM is ambiguous.
        return _v(TimeOfDayValue(hour=h, minute=0, grain=Grain.HOUR, latent=True))

    return Rule(name=f"word-hour:{base_hour}", pattern=(regex(_clock_head_re(pat)),), prod=prod)


# ---------------------------------------------------------------------------
# "الساعة <X>" — numeric or word hour with the o'clock marker, non-latent.

_HOUR_NUM_RE = _numeric_re(r"([0-9٠-٩]{1,2})")
_OCLOCK_RE = r"(?:ال)?ساع[ةه]"


def _prod_oclock_numeric(matched: tuple[Token, ...]) -> Token | None:
    rm = _regex_match(matched[0])
    if rm is None or rm.groups[0] is None:
        return None
    try:
        h = parse_arabic_int(rm.groups[0])
    except ValueError:
        return None
    if not (0 <= h <= 23):
        return None
    return _v(TimeOfDayValue(hour=h, minute=0, grain=Grain.HOUR))


_oclock_numeric_rule = Rule(
    name="الساعة <H>",
    pattern=(regex(rf"{_word_re(_OCLOCK_RE)}\s+{_HOUR_NUM_RE}{_CLOCK_CONTINUATION_GUARD}"),),
    prod=_prod_oclock_numeric,
)


def _prod_oclock_word(matched: tuple[Token, ...]) -> Token | None:
    inner = matched[1]
    if not _is_clock(inner):
        return None
    tod: TimeOfDayValue = inner.value
    return _v(replace(tod, latent=False))


_oclock_word_rule = Rule(
    name="الساعة <word-hour>",
    pattern=(regex(_word_re(_OCLOCK_RE)), predicate(_is_clock, "is_clock")),
    prod=_prod_oclock_word,
)


# ---------------------------------------------------------------------------
# Noon / midnight — fixed hour-grain instants.


def _prod_noon(_: tuple[Token, ...]) -> Token:
    return _v(TimeOfDayValue(hour=12, minute=0, grain=Grain.HOUR))


def _prod_midnight(_: tuple[Token, ...]) -> Token:
    return _v(TimeOfDayValue(hour=0, minute=0, grain=Grain.HOUR))


_noon_rule = Rule(
    name="noon",
    pattern=(regex(_word_re(r"منتصف\s+النهار")),),
    prod=_prod_noon,
)

_midnight_rule = Rule(
    name="midnight",
    pattern=(regex(_word_re(r"منتصف\s+الليل")),),
    prod=_prod_midnight,
)


# ---------------------------------------------------------------------------
# AM / PM modifiers applied to a numeric or word hour.
#
# Convention:
#   AM  (صباحا/الصبح/فجرا): 12-hour H stays in 0-11. "12 صباحا" → 0.
#   PM  (مساء/ليلا/بعد الظهر/ظهرا/عصرا/بعد المغرب): 12-hour H maps to H+12.
#   For 24-hour H (>= 13) the suffix is treated as a tag; we keep H as-is.

# "قبل الظهر" (before noon) is AM-equivalent and lives in `_AM_RE`.
_AM_RE = _word_re(r"(?:صباحا?|الصبح|فجرا?|قبل\s+الظهر)")
_PM_RE = _word_re(r"(?:مساءا?|ليلا?|بعد\s+الظهر|بعد\s+المغرب|عصرا?|ظهرا?)")


def _to_am(hour: int) -> int:
    # 12 AM → 0; 1-11 AM stay; 24h hours pass through unchanged.
    return 0 if hour == 12 else hour


def _to_pm(hour: int) -> int:
    # 1-11 PM → +12; 12 PM stays; 24h hours pass through unchanged.
    return hour + 12 if 1 <= hour <= 11 else hour


def _hour_from_match(rm: RegexMatch, group_idx: int) -> int | None:
    raw = rm.groups[group_idx] if group_idx < len(rm.groups) else None
    if raw is None:
        return None
    try:
        return parse_arabic_int(raw)
    except ValueError:
        return None


def _prod_numeric_am(matched: tuple[Token, ...]) -> Token | None:
    rm = _regex_match(matched[0])
    if rm is None:
        return None
    h = _hour_from_match(rm, 0)
    if h is None or not (0 <= h <= 23):
        return None
    return _v(TimeOfDayValue(hour=_to_am(h), minute=0, grain=Grain.HOUR))


def _prod_numeric_pm(matched: tuple[Token, ...]) -> Token | None:
    rm = _regex_match(matched[0])
    if rm is None:
        return None
    h = _hour_from_match(rm, 0)
    if h is None or not (0 <= h <= 23):
        return None
    return _v(TimeOfDayValue(hour=_to_pm(h), minute=0, grain=Grain.HOUR))


_numeric_am_rule = Rule(
    name="<H> <am>",
    pattern=(regex(rf"{_HOUR_NUM_RE}\s+{_AM_RE}"),),
    prod=_prod_numeric_am,
)

_numeric_pm_rule = Rule(
    name="<H> <pm>",
    pattern=(regex(rf"{_HOUR_NUM_RE}\s+{_PM_RE}"),),
    prod=_prod_numeric_pm,
)


# "<word-hour> صباحا/مساء/..." — applied to an existing TimeOfDayValue token.


def _prod_clock_am(matched: tuple[Token, ...]) -> Token | None:
    inner = matched[0]
    if not _is_clock(inner):
        return None
    tod: TimeOfDayValue = inner.value
    new_hour = _to_am(tod.hour)
    return _v(replace(tod, hour=new_hour, latent=False))


def _prod_clock_pm(matched: tuple[Token, ...]) -> Token | None:
    inner = matched[0]
    if not _is_clock(inner):
        return None
    tod: TimeOfDayValue = inner.value
    new_hour = _to_pm(tod.hour)
    return _v(replace(tod, hour=new_hour, latent=False))


_clock_am_rule = Rule(
    name="<clock> <am>",
    pattern=(predicate(_is_clock, "is_clock"), regex(_AM_RE)),
    prod=_prod_clock_am,
)

_clock_pm_rule = Rule(
    name="<clock> <pm>",
    pattern=(predicate(_is_clock, "is_clock"), regex(_PM_RE)),
    prod=_prod_clock_pm,
)


# ---------------------------------------------------------------------------
# Half / quarter modifiers: "<clock> و نصف", "<clock> و ربع", "<clock> الا ربع".
#
# These shift minutes; grain becomes minute. Hour-mod is handled to keep H in
# 0-23 (e.g. "12 الا ربع" → 11:45).


def _shift(tod: TimeOfDayValue, delta_min: int) -> TimeOfDayValue:
    total = (tod.hour * 60 + tod.minute + delta_min) % (24 * 60)
    return TimeOfDayValue(
        hour=total // 60,
        minute=total % 60,
        grain=Grain.MINUTE,
        latent=False,
    )


def _prod_half_past(matched: tuple[Token, ...]) -> Token | None:
    inner = matched[0]
    if not _is_clock(inner):
        return None
    return _v(_shift(inner.value, 30))


def _prod_quarter_past(matched: tuple[Token, ...]) -> Token | None:
    inner = matched[0]
    if not _is_clock(inner):
        return None
    return _v(_shift(inner.value, 15))


def _prod_quarter_to(matched: tuple[Token, ...]) -> Token | None:
    inner = matched[0]
    if not _is_clock(inner):
        return None
    return _v(_shift(inner.value, -15))


_half_past_rule = Rule(
    name="<clock> و نصف",
    pattern=(
        predicate(_is_clock, "is_clock"),
        regex(_word_re(r"و\s*نصف(?:\s+ساع[ةه])?")),
    ),
    prod=_prod_half_past,
)

_quarter_past_rule = Rule(
    name="<clock> و ربع",
    pattern=(
        predicate(_is_clock, "is_clock"),
        regex(_word_re(r"و\s*ربع(?:\s+ساع[ةه])?")),
    ),
    prod=_prod_quarter_past,
)

_quarter_to_rule = Rule(
    name="<clock> الا ربع",
    pattern=(
        predicate(_is_clock, "is_clock"),
        regex(_word_re(r"[إا]لا\s+ربعا?")),
    ),
    prod=_prod_quarter_to,
)


# ---------------------------------------------------------------------------
# "<H> و <M> دقيقة" — explicit minute appendage to an existing clock hour.

_MIN_RE = r"([0-9٠-٩]{1,2})"


def _prod_clock_and_minutes(matched: tuple[Token, ...]) -> Token | None:
    inner = matched[0]
    if not _is_clock(inner):
        return None
    rm = _regex_match(matched[1])
    if rm is None or rm.groups[0] is None:
        return None
    try:
        m = parse_arabic_int(rm.groups[0])
    except ValueError:
        return None
    if not (0 <= m < 60):
        return None
    return _v(_shift(inner.value, m))


_clock_and_minutes_rule = Rule(
    name="<clock> و <M> دقيقة",
    pattern=(
        predicate(_is_clock, "is_clock"),
        regex(_word_re(rf"و\s*{_MIN_RE}\s+(?:دقيق[ةه]|دقائق)")),
    ),
    prod=_prod_clock_and_minutes,
)


# ---------------------------------------------------------------------------
# Rule list assembly.

RULES: tuple[Rule, ...] = (
    # Word-form hours (latent until anchored).
    *(_make_word_hour_rule(p, h) for (p, h) in _WORD_HOURS),
    # "الساعة" anchors.
    _oclock_numeric_rule,
    _oclock_word_rule,
    # Noon / midnight.
    _noon_rule,
    _midnight_rule,
    # AM/PM applied to numeric hours directly.
    _numeric_am_rule,
    _numeric_pm_rule,
    # AM/PM composed onto an existing clock token (covers word hours + hh:mm).
    _clock_am_rule,
    _clock_pm_rule,
    # Half / quarter modifiers.
    _half_past_rule,
    _quarter_past_rule,
    _quarter_to_rule,
    # Explicit minutes.
    _clock_and_minutes_rule,
    # TODO(puckling): edge case — "ثلث" (one third / 20 min past).
    # TODO(puckling): edge case — "الساعة الثانية عشرة و النصف" (multi-token chains
    #   without spaces around connectives).
    # TODO(puckling): edge case — locale-specific "هذه الليلة" anchoring evening hours.
)
