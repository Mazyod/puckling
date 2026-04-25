"""Supplemental English clock-time rules.

These rules fill coverage gaps left by the main `time/en/rules.py` for
clock-time phrases. The registry auto-discovers any `<topic>_rules.py` and
merges its `RULES` into the global ruleset, so this module participates in
`parse()` automatically without any edit to existing files.

Coverage added:
- "half past <H>", "quarter past <H>", "quarter to <H>" with bare digit or
  word hours (e.g. "half past five", "half past 5") — promoted to non-latent.
- British "half <H>" (= half past <H>).
- "<n> minutes past/to <H>" (explicit "minutes" word).
- "<n> past/to <H>" — e.g. "twenty past 5", "10 past 5".
- 24-hour h-prefixed forms: "17h", "17h00", "17h30", "5h".
- "<H> <MM-word>" — e.g. "five thirty", "two thirty pm".
- Extra precision modifiers: "around", "exactly", "approximately", etc.,
  plus postfix "sharp" / "on the dot".
- "twelve noon" / "twelve midnight" explicit forms.
"""

from __future__ import annotations

from puckling.dimensions.time.en._helpers import (
    RelTime,
    hour_minute_value,
    hour_value,
    shift_minutes,
)
from puckling.dimensions.time.grain import Grain
from puckling.predicates import is_time
from puckling.types import RegexMatch, Rule, Token, predicate, regex

# ---------------------------------------------------------------------------
# Token helpers


def _tt(value: RelTime) -> Token:
    return Token(dim="time", value=value)


def _is_hour_or_minute(t: Token) -> bool:
    if t.dim != "time":
        return False
    grain = getattr(t.value, "grain", None)
    return grain in (Grain.HOUR, Grain.MINUTE)


# Word -> integer for spelled-out small numbers used in clock contexts.
_HOUR_WORDS: dict[str, int] = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12,
}
_HOUR_WORD_PATTERN = "|".join(_HOUR_WORDS.keys())

# Cardinal word values for minutes — common shapes used in constructions
# like "twenty past five" / "ten to noon" / "five thirty".
_MINUTE_WORDS: dict[str, int] = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "twenty-five": 25, "twenty five": 25,
    "thirty": 30, "thirty-five": 35, "thirty five": 35, "forty": 40,
    "forty-five": 45, "forty five": 45, "fifty": 50,
    "fifty-five": 55, "fifty five": 55,
    "twentyfive": 25, "thirtyfive": 35, "fortyfive": 45, "fiftyfive": 55,
}
# Sort longest-first so multi-word forms ("twenty five") are preferred over
# their bare prefixes ("twenty") when alternation matches greedily.
_MINUTE_WORD_PATTERN = "|".join(sorted(_MINUTE_WORDS, key=len, reverse=True))

_HOUR_DIGIT_OR_WORD = r"\d{1,2}|" + _HOUR_WORD_PATTERN
_MINUTE_DIGIT_OR_WORD = r"\d{1,2}|" + _MINUTE_WORD_PATTERN
_AMPM = r"([ap])\.?m?\.?"


def _parse_int_or_word(text: str, words: dict[str, int]) -> int | None:
    text = text.lower().strip()
    if text.isdigit():
        return int(text)
    return words.get(text)


def _hour_at(tokens: tuple[Token, ...], idx: int) -> int | None:
    """Extract a 1..12 hour value from a digit-or-word regex token."""
    m = tokens[idx].value
    if not isinstance(m, RegexMatch):
        return None
    h = _parse_int_or_word(m.text, _HOUR_WORDS)
    if h is None or not 1 <= h <= 12:
        return None
    return h


def _minute_at(tokens: tuple[Token, ...], idx: int) -> int | None:
    """Extract a 1..59 minute value from a digit-or-word regex token."""
    m = tokens[idx].value
    if not isinstance(m, RegexMatch):
        return None
    n = _parse_int_or_word(m.text, _MINUTE_WORDS)
    if n is None or not 1 <= n <= 59:
        return None
    return n


def _ampm_at(tokens: tuple[Token, ...], idx: int) -> bool | None:
    """Return True if `am`, False if `pm`, None when missing."""
    if idx >= len(tokens):
        return None
    m = tokens[idx].value
    if not isinstance(m, RegexMatch):
        return None
    text = m.text.lower()
    if text.startswith("a"):
        return True
    if text.startswith("p"):
        return False
    return None


def _build_clock(base_h: int, minute_offset: int, ampm: bool | None) -> RelTime:
    """Build a non-latent clock-time `minute_offset` away from `base_h`."""
    if ampm is None:
        base = hour_value(base_h, is_12h=True)
    else:
        final_h = base_h % 12 + (0 if ampm else 12)
        base = hour_value(final_h, is_12h=False)
    if minute_offset == 0:
        return base.not_latent()
    return shift_minutes(base, minute_offset).not_latent()


def _make_offset_prod(hour_idx: int, minute_offset: int, ampm_idx: int | None):
    """Build a production that resolves `<hour at hour_idx> + minute_offset`.

    `ampm_idx`, when set, picks an AM/PM suffix token; otherwise the hour
    is resolved as 12-hour latent (Duckling chooses the next future match).
    """

    def prod(tokens: tuple[Token, ...]) -> Token | None:
        h = _hour_at(tokens, hour_idx)
        if h is None:
            return None
        ampm = _ampm_at(tokens, ampm_idx) if ampm_idx is not None else None
        return _tt(_build_clock(h, minute_offset, ampm))

    return prod


def _make_minute_offset_prod(
    minute_idx: int, hour_idx: int, sign: int, *, has_minutes_word: bool
):
    """Build a production for "<n> [minutes] past/to <H>" forms."""

    def prod(tokens: tuple[Token, ...]) -> Token | None:
        n = _minute_at(tokens, minute_idx)
        if n is None:
            return None
        h = _hour_at(tokens, hour_idx)
        if h is None:
            return None
        return _tt(_build_clock(h, sign * n, None))

    # Tag the closure for debuggability.
    prod.__name__ = (
        f"<n>{'_minutes' if has_minutes_word else ''}_"
        f"{'past' if sign > 0 else 'to'}_<H>"
    )
    return prod


# ---------------------------------------------------------------------------
# half / quarter past/to with explicit numeral hour (digit or word)

_HALF_PREFIX = r"half\s+(?:past|after)"
_QUARTER_PAST_PREFIX = r"(?:a\s+)?quarter\s+(?:past|after)"
_QUARTER_TO_PREFIX = r"(?:a\s+)?quarter\s+(?:to|till|before|of)"


def _make_offset_rules(
    name: str, prefix_pat: str, minute_offset: int
) -> tuple[Rule, Rule]:
    """One rule with a trailing am/pm, one without — share the same production."""
    with_ampm = Rule(
        name=f"{name} <H-num> am/pm",
        pattern=(regex(prefix_pat), regex(_HOUR_DIGIT_OR_WORD), regex(_AMPM)),
        prod=_make_offset_prod(hour_idx=1, minute_offset=minute_offset, ampm_idx=2),
    )
    bare = Rule(
        name=f"{name} <H-num>",
        pattern=(regex(prefix_pat), regex(_HOUR_DIGIT_OR_WORD)),
        prod=_make_offset_prod(hour_idx=1, minute_offset=minute_offset, ampm_idx=None),
    )
    return with_ampm, bare


_half_past_rules = _make_offset_rules("half past", _HALF_PREFIX, 30)
_quarter_past_rules = _make_offset_rules("quarter past", _QUARTER_PAST_PREFIX, 15)
_quarter_to_rules = _make_offset_rules("quarter to", _QUARTER_TO_PREFIX, -15)


# ---------------------------------------------------------------------------
# British "half five" — colloquial for "half past 5"
#
# TODO(puckling): edge case — "half five" in German/Dutch means 4:30 (half
# *to* five), not 5:30; we follow the British reading here. Locale-specific
# overrides could revisit this.

_british_half_rule = Rule(
    name="half <H> (British 'half five')",
    pattern=(regex(r"half"), regex(_HOUR_DIGIT_OR_WORD)),
    prod=_make_offset_prod(hour_idx=1, minute_offset=30, ampm_idx=None),
)


# ---------------------------------------------------------------------------
# "<n> minutes past/to <H>" — explicit "minutes" word

_n_minutes_past_rule = Rule(
    name="<n> minutes past <H>",
    pattern=(
        regex(_MINUTE_DIGIT_OR_WORD),
        regex(r"min(?:ute)?s?"),
        regex(r"past|after"),
        regex(_HOUR_DIGIT_OR_WORD),
    ),
    prod=_make_minute_offset_prod(0, 3, +1, has_minutes_word=True),
)

_n_minutes_to_rule = Rule(
    name="<n> minutes to <H>",
    pattern=(
        regex(_MINUTE_DIGIT_OR_WORD),
        regex(r"min(?:ute)?s?"),
        regex(r"to|till|before|of"),
        regex(_HOUR_DIGIT_OR_WORD),
    ),
    prod=_make_minute_offset_prod(0, 3, -1, has_minutes_word=True),
)


# ---------------------------------------------------------------------------
# "<n> past/to <H>" — e.g. "twenty past 5", "10 past 5".
# Complements the main rules' equivalent which requires an existing
# hour-grain time token; here we accept a bare digit/word hour.

_bare_n_past_n_rule = Rule(
    name="<n-num> past <H-num>",
    pattern=(
        regex(_MINUTE_DIGIT_OR_WORD),
        regex(r"past|after"),
        regex(_HOUR_DIGIT_OR_WORD),
    ),
    prod=_make_minute_offset_prod(0, 2, +1, has_minutes_word=False),
)

_bare_n_to_n_rule = Rule(
    name="<n-num> to <H-num>",
    pattern=(
        regex(_MINUTE_DIGIT_OR_WORD),
        regex(r"to|till|before"),
        regex(_HOUR_DIGIT_OR_WORD),
    ),
    prod=_make_minute_offset_prod(0, 2, -1, has_minutes_word=False),
)


# ---------------------------------------------------------------------------
# 24-hour "h" form: "17h", "17h30", "23h00", "5h"


def _h_separator_prod(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[0].value
    if not isinstance(m, RegexMatch):
        return None
    raw_hour = m.groups[0] if len(m.groups) > 0 else None
    if raw_hour is None:
        return None
    h = int(raw_hour)
    if not 0 <= h <= 23:
        return None
    raw_min = m.groups[1] if len(m.groups) > 1 else None
    if raw_min is None:
        return _tt(hour_value(h, is_12h=False))
    mn = int(raw_min)
    return _tt(hour_minute_value(h, mn, is_12h=False))


_h_separator_rule = Rule(
    name="<H>h<MM>",
    pattern=(regex(r"((?:[01]?\d)|(?:2[0-3]))h([0-5]\d)?\b"),),
    prod=_h_separator_prod,
)


# ---------------------------------------------------------------------------
# "<H> <MM-word> [am/pm]" — e.g. "five thirty", "two thirty pm"


def _hour_minute_word_prod(tokens: tuple[Token, ...]) -> Token | None:
    h_match = tokens[0].value
    mn_match = tokens[1].value
    if not isinstance(h_match, RegexMatch) or not isinstance(mn_match, RegexMatch):
        return None
    h = _parse_int_or_word(h_match.text, _HOUR_WORDS)
    if h is None or not 1 <= h <= 12:
        return None
    mn = _MINUTE_WORDS.get(mn_match.text.lower().strip())
    if mn is None:
        return None
    ampm = _ampm_at(tokens, 2)
    if ampm is None:
        return _tt(hour_minute_value(h, mn, is_12h=True))
    final_h = h % 12 + (0 if ampm else 12)
    return _tt(hour_minute_value(final_h, mn, is_12h=False))


_hour_minute_word_ampm_rule = Rule(
    name="<H> <MM-word> am/pm",
    pattern=(
        regex(_HOUR_DIGIT_OR_WORD),
        regex(_MINUTE_WORD_PATTERN),
        regex(_AMPM),
    ),
    prod=_hour_minute_word_prod,
)

_hour_minute_word_rule = Rule(
    name="<H> <MM-word>",
    pattern=(regex(_HOUR_DIGIT_OR_WORD), regex(_MINUTE_WORD_PATTERN)),
    prod=_hour_minute_word_prod,
)


# ---------------------------------------------------------------------------
# Precision modifiers — extra adverbs on top of the main "at <time>" rule.


def _precision_prod(tokens: tuple[Token, ...]) -> Token | None:
    inner = tokens[1]
    if inner.dim != "time":
        return None
    return _tt(inner.value.not_latent())


_precision_rule = Rule(
    name="<precision-modifier> <time>",
    pattern=(
        regex(
            r"(?:around|approximately|approx\.?|roughly|about|exactly|"
            r"precisely|right\s+at|right\s+around|sharp\s+at|circa)"
        ),
        predicate(is_time, "is_time"),
    ),
    prod=_precision_prod,
)


def _sharp_prod(tokens: tuple[Token, ...]) -> Token | None:
    inner = tokens[0]
    if inner.dim != "time":
        return None
    return _tt(inner.value.not_latent())


_sharp_rule = Rule(
    name="<time> sharp/exactly",
    pattern=(
        predicate(_is_hour_or_minute, "is_hour_or_minute"),
        regex(r"sharp|exactly|on the dot"),
    ),
    prod=_sharp_prod,
)


# ---------------------------------------------------------------------------
# "twelve noon" / "twelve midnight" — explicit hour anchor.


def _twelve_noon_prod(tokens: tuple[Token, ...]) -> Token | None:
    m = tokens[1].value
    if not isinstance(m, RegexMatch):
        return None
    if "noon" in m.text.lower():
        return _tt(hour_value(12, is_12h=False))
    return _tt(hour_value(0, is_12h=False))


_twelve_noon_rule = Rule(
    name="twelve noon|midnight",
    pattern=(regex(r"twelve|12"), regex(r"noon|midni(?:ght|te)")),
    prod=_twelve_noon_prod,
)


# ---------------------------------------------------------------------------
# Aggregate

RULES: tuple[Rule, ...] = (
    *_half_past_rules,
    *_quarter_past_rules,
    *_quarter_to_rules,
    _british_half_rule,
    _n_minutes_past_rule,
    _n_minutes_to_rule,
    _bare_n_past_n_rule,
    _bare_n_to_n_rule,
    _h_separator_rule,
    _hour_minute_word_ampm_rule,
    _hour_minute_word_rule,
    _precision_rule,
    _sharp_rule,
    _twelve_noon_rule,
)
