"""Regressions for review-flagged defects.

Each test here would fail against the pre-fix code:

1. AR time dedupe — `WrappedTimeData` equality previously delegated to
   `TimeData`'s default dataclass equality, which compares the closure-backed
   `predicate` field. Two structurally identical AR time tokens produced by
   separate rule firings compared unequal, so the engine could not dedupe
   them and saturated under composition.
2. AR distance/temperature unit regexes — bare `م` and bare `س` matched as
   single-letter unit abbreviations without a word boundary, so they fired
   inside arbitrary Arabic words (e.g. `ميل`, `سيارة`) and produced spurious
   distance/temperature entities.
3. `is_positive` predicate — used `> 0`, diverging from upstream Duckling's
   `isPositive` (`>= 0`). Made `-0` (and `negative 0` / `minus 0`) reject
   under the negative-numbers rule, leaving a wrong parse.
"""

from __future__ import annotations

from enum import Enum

import pytest

from puckling import Options, parse
from puckling.api import analyze
from puckling.dimensions.time.ar._helpers import WrappedTimeData
from puckling.dimensions.time.grain import Grain
from puckling.dimensions.time.helpers import at_day_of_week, time
from puckling.predicates import is_positive
from puckling.types import Token

# ---------------------------------------------------------------------------
# Fix 1 — AR time dedupe via stable key.


def _make_keyed_dow(weekday: int) -> WrappedTimeData:
    """Mirror the AR rule's per-firing TimeData construction with a stable key."""
    td = time(at_day_of_week(weekday), Grain.DAY)
    return WrappedTimeData(inner=td, key=("dow", weekday))


def test_ar_time_dedupes_across_rule_firings():
    """Two structurally-identical AR time values built from independent closures
    must compare equal and hash equal once they carry the same semantic key.
    Without the fix, the inner `TimeData.predicate` lambdas had distinct
    identities, so default equality returned False and the engine retained
    duplicate tokens.
    """
    a = _make_keyed_dow(0)  # Monday, fresh closure
    b = _make_keyed_dow(0)  # Monday, fresh closure (different lambda object)
    assert a.inner.predicate is not b.inner.predicate, (
        "test premise: predicates must be distinct closures"
    )
    assert a == b
    assert hash(a) == hash(b)


def test_ar_time_keeps_distinct_values_distinct():
    """Different semantic keys must NOT collapse — Monday and Tuesday remain
    distinct tokens even though they share grain/latent/holiday."""
    monday = _make_keyed_dow(0)
    tuesday = _make_keyed_dow(1)
    assert monday != tuesday
    assert hash(monday) != hash(tuesday)


def test_ar_time_token_dedupes_in_parse_forest(ctx_ar):
    """End-to-end: parsing `اثنين` (Monday, no `ال` prefix) must produce
    exactly one resolved time token in the analyze forest. Pre-fix, every
    saturation iteration produced a fresh `WrappedTimeData` whose inner
    `TimeData.predicate` lambda had a new identity, so the engine accumulated
    50× duplicates (one per saturation iteration up to the iteration cap)
    instead of deduping.

    `analyze` returns all resolved tokens (including overlaps) — this surfaces
    the duplicates that `parse()`'s longest-non-overlapping winner selection
    would otherwise hide. The unprefixed form is used so that the regex
    `(?:ال)?[اإ]ثنين` only matches at one position; with the `ال` prefix
    the regex would match twice (positions 0 and 2) which would muddle the
    differential count.
    """
    resolved = analyze("اثنين", ctx_ar, Options(), dims=("time",))
    monday_tokens = [r for r in resolved if r.dim == "time"]
    assert len(monday_tokens) == 1, (
        f"expected single Monday token after dedupe; got {len(monday_tokens)} duplicates"
    )


# ---------------------------------------------------------------------------
# Fix 2 — Tightened AR unit regexes.


def _unit_of(entity) -> str | None:
    """Pull a unit string out of a structured runtime value."""
    unit = getattr(entity.value, "unit", None)
    if isinstance(unit, Enum):
        return str(unit.value)
    return unit


def test_ar_distance_bare_meem_does_not_match_inside_word(ctx_ar):
    """`5 ملاك` ("5 angels"/"5 owners") must NOT surface a metre entity from
    the leading `م` of `ملاك`.

    Previously the metre regex `أمتار|متر(ات)?|م` matched the bare `م`
    prefix without a word boundary, producing a stray METRE entity covering
    `5 م`. No competing unit rule shadows this in `5 ملاك`, so longest-match
    selection cannot mask the bug — the spurious METRE entity surfaces in
    the result.
    """
    out = parse("5 ملاك", ctx_ar, Options(), dims=("distance",))
    distance = [e for e in out if e.dim == "distance"]
    metre_entities = [e for e in distance if str(_unit_of(e) or "").lower() == "metre"]
    assert not metre_entities, (
        f"bare 'م' incorrectly matched as METRE inside 'ملاك': {distance!r}"
    )


def test_ar_distance_bare_meem_still_matches_at_word_end(ctx_ar):
    """`5 م` (m as a standalone abbreviation) must still parse as METRE —
    the word boundary fix preserves the legitimate use."""
    out = parse("5 م", ctx_ar, Options(), dims=("distance",))
    distance = [e for e in out if e.dim == "distance"]
    assert distance, "bare 'م' followed by end-of-text should parse as a distance"
    assert any(str(_unit_of(e) or "").lower() == "metre" for e in distance), (
        f"expected metre unit; got {distance!r}"
    )


def test_ar_temperature_bare_seen_does_not_match_without_degree(ctx_ar):
    """`5 سيارة` must NOT produce a celsius entity from the leading `س`.

    Previously the celsius regex `درجة\\s+مئوية|°?\\s*س` made `°` optional,
    so a bare `س` after a numeral surfaced a celsius token despite `س`
    alone not being a standard celsius abbreviation.
    """
    out = parse("5 سيارة", ctx_ar, Options(), dims=("temperature",))
    celsius_temps = [
        e for e in out
        if e.dim == "temperature" and str(_unit_of(e) or "").lower() == "celsius"
    ]
    assert not celsius_temps, (
        f"bare 'س' incorrectly matched as CELSIUS inside 'سيارة': {celsius_temps!r}"
    )


def test_ar_temperature_degree_seen_still_matches(ctx_ar):
    """`5 °س` (degrees + س, with whitespace tolerated) must still parse as
    CELSIUS — the explicit `°` abbreviation is preserved by the fix."""
    out = parse("5 °س", ctx_ar, Options(), dims=("temperature",))
    celsius_temps = [
        e for e in out
        if e.dim == "temperature" and str(_unit_of(e) or "").lower() == "celsius"
    ]
    assert celsius_temps, f"'5 °س' should parse as celsius; got {out!r}"


# ---------------------------------------------------------------------------
# Fix 3 — `is_positive` parity with Duckling's `isPositive` (>= 0, not > 0).


def _numeral_token(value: int | float) -> Token:
    from puckling.dimensions.numeral.types import NumeralValue
    from puckling.types import Range

    return Token(dim="numeral", value=NumeralValue(value=value), range=Range(0, 1))


def test_is_positive_admits_zero():
    """Upstream Duckling's `isPositive` returns True for zero; pre-fix the
    local predicate used strict `> 0` which rejected zero and prevented the
    `negative <numeral>` rule from firing on `-0` / `minus 0`."""
    assert is_positive(_numeral_token(0)) is True
    assert is_positive(_numeral_token(0.0)) is True
    assert is_positive(_numeral_token(5)) is True
    # Negative values must still be rejected.
    assert is_positive(_numeral_token(-1)) is False


def test_negative_zero_parses_under_negative_rule(ctx_en):
    """`negative 0` must compose into a numeral token whose body covers the
    full `negative 0` span. Pre-fix, `is_positive(0)` returned False, so the
    `negative <is_positive>` rule never fired — the `0` was still parsed as a
    bare numeral but the leading `negative` was dropped (body would be just
    `0`). The fix surfaces the full phrase as one negated-numeral entity.
    """
    out = parse("negative 0", ctx_en, Options(), dims=("numeral",))
    numerals = [e for e in out if e.dim == "numeral"]
    assert numerals, f"expected a numeral entity; got {out!r}"
    bodies = {e.body for e in numerals}
    assert "negative 0" in bodies, (
        f"expected `negative 0` body (full negation span); got bodies {bodies!r}"
    )


@pytest.mark.parametrize("phrase", ["minus 0", "negative 0", "-0"])
def test_negation_of_zero_covers_full_span(ctx_en, phrase):
    """All three negation forms must absorb the leading `-`/`minus`/`negative`
    into a single numeral entity covering the whole phrase. Pre-fix, the
    word forms (`minus 0`, `negative 0`) split into a stray prefix + a bare
    `0` numeral because `is_positive(0)` rejected the operand.
    """
    out = parse(phrase, ctx_en, Options(), dims=("numeral",))
    numerals = [e for e in out if e.dim == "numeral"]
    assert any(e.body == phrase for e in numerals), (
        f"expected one numeral covering `{phrase}`; got {numerals!r}"
    )
