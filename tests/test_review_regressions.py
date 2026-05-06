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
4. Dim filter dropped cross-dim deps — registry filtered rules at load time,
   so requesting `dims=("amount_of_money", "time")` excluded numeral rules
   that money's `<currency> <amount>` rule transitively needs to recognise
   fractions/decimals. `$1/2`, `$10/1`, AR `20.43 $`-in-compound silently
   downgraded to a time match. Fix: registry expands `dims` to its
   dependency closure before loading rules.
5. Hour-word regex (`one|two|...|twelve`) lacked word boundaries, so the
   single-regex `<word-H>` rule fired on the `four` prefix of `fourth`,
   composing a spurious time span.
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


# ---------------------------------------------------------------------------
# Fix 4 — Registry expands `dims` to its dependency closure before loading rules.


@pytest.mark.parametrize(
    "text, expected_body",
    [
        ("$1/2", "$1/2"),
        ("$10/1", "$10/1"),
        ("$ 10/1", "$ 10/1"),
    ],
)
def test_money_with_fractional_amount_under_dim_filter(ctx_en, text, expected_body):
    """`$1/2`-style amounts must surface as money when caller filters to
    `("amount_of_money", "time")`. Pre-fix, the registry stripped the
    `numeral` rules out at load time, so the `fractional number` rule never
    fired, the money `<currency> <amount>` chain bottomed out at `$1`, and
    the `mm/dd` time rule absorbed the leftover `1/2`.
    """
    result = parse(text, ctx_en, Options(), dims=("amount_of_money", "time"))
    money_bodies = {e.body for e in result if e.dim == "amount_of_money"}
    assert expected_body in money_bodies, (
        f"expected money body {expected_body!r}; got {[(e.dim, e.body) for e in result]!r}"
    )


def test_ar_postfix_dollar_in_compound_under_dim_filter(ctx_ar):
    """`20.43 $` after a non-money token must still parse as money under
    `dims=("amount_of_money", "time")`. Pre-fix, the AR numeral rule for
    decimals (`integer (numeric, ar/en digits)`) was stripped from the rule
    set, so `20.43` was only seen by the `hh:mm` time rule and money was
    suppressed.
    """
    text = "رابع,20.43 $"
    result = parse(text, ctx_ar, Options(), dims=("amount_of_money", "time"))
    money_bodies = {e.body for e in result if e.dim == "amount_of_money"}
    assert "20.43 $" in money_bodies, (
        f"expected money '20.43 $'; got {[(e.dim, e.body) for e in result]!r}"
    )


# ---------------------------------------------------------------------------
# Fix 5 — `<word-H>` hour-word pattern anchors at word boundaries.


def test_money_intersect_absorbs_fractional_date_suffix(ctx_en):
    """`KWD 3 2026/02/02` must surface as one money span covering
    `KWD 3 2026/02` (matching upstream Duckling). Pre-fix, the intersect
    rule's `is_natural` predicate rejected the fractional numeral
    `2026/02` (=1013.0, a float), so money stopped at `KWD 3 2026` and
    the leftover `02/02` re-fired as a spurious `mm/dd` time span.
    The fix uses an `is_positive AND not has_grain` predicate so the
    fractional cents-cast is admitted.
    """
    result = parse(
        "KWD 3 2026/02/02", ctx_en, Options(), dims=("amount_of_money", "time")
    )
    bodies = {(e.dim, e.body) for e in result}
    assert ("amount_of_money", "KWD 3 2026/02") in bodies, (
        f"expected money 'KWD 3 2026/02'; got {sorted(bodies)!r}"
    )
    time_bodies = {b for d, b in bodies if d == "time"}
    assert "02/02" not in time_bodies, (
        f"spurious mm/dd time span surfaced: {sorted(bodies)!r}"
    )


# ---------------------------------------------------------------------------
# Production-data parity (AR). Each row is a real input that returned `[]`
# before the fix and a non-empty entity in upstream Duckling.


def test_ar_phone_with_masked_card_suffix(ctx_ar):
    """`078654xxxxxx3001` (masked-card pipeline output) must surface a
    phone span on the leading 6 digits. Pre-fix, the phone right boundary
    rejected a trailing letter, so duck's `phone-number 078654` had no
    counterpart.
    """
    text = "حولي الي بطاقه 078654xxxxxx3001"
    result = parse(text, ctx_ar, Options(), dims=("phone_number",))
    bodies = {(e.dim, e.body) for e in result}
    assert ("phone_number", "078654") in bodies, (
        f"expected phone '078654'; got {sorted(bodies)!r}"
    )


def test_ar_money_iso_prefix(ctx_ar):
    """`aed 2,420.00` (bank-ledger format, ISO code on the left) must
    surface as a money span. Pre-fix, AR money only had `<n> <ISO>`; the
    ISO-prefix form was unmatched.
    """
    text = "حولي الي دينار الكويتي جم aed 2,420.00"
    result = parse(text, ctx_ar, Options(), dims=("amount_of_money",))
    bodies = {(e.dim, e.body) for e in result}
    assert ("amount_of_money", "aed 2,420.00") in bodies, (
        f"expected money 'aed 2,420.00'; got {sorted(bodies)!r}"
    )


def test_ar_weekday_with_proclitic_prefix(ctx_ar):
    """`حولي لاحد` ('transfer to/for Sunday') must surface a time span on
    `احد`. Pre-fix, the weekday rule's left boundary rejected the
    proclitic `ل` prefix; only `و` was treated as separable.
    """
    text = "حولي لاحد"
    result = parse(text, ctx_ar, Options(), dims=("time",))
    bodies = {(e.dim, e.body) for e in result}
    assert ("time", "احد") in bodies, (
        f"expected time 'احد'; got {sorted(bodies)!r}"
    )


def test_ar_part_of_day_surfaces_without_with_latent(ctx_ar):
    """`سلام عليكم مساء الخير` must surface a `time` entity for `مساء`
    even with default `Options()`. Pre-fix, AR `PartOfDayInterval` was
    `latent=True`, so callers had to opt in via `with_latent=True`;
    upstream Duckling has no latent concept and surfaces the entity by
    default in production data.
    """
    text = "سلام عليكم مساء الخير"
    result = parse(text, ctx_ar, Options(), dims=("time",))
    bodies = {(e.dim, e.body) for e in result}
    assert ("time", "مساء") in bodies, (
        f"expected time 'مساء'; got {sorted(bodies)!r}"
    )


def test_ar_duration_with_definite_article_prefix(ctx_ar):
    """`مسابقه تحدي الدقيقه` must extract `دقيقه` from inside the definite
    article `ال` proclitic. Pre-fix, the duration rule's left boundary
    rejected the `ل`, so `الدقيقه`/`الساعة`/`اليوم` couldn't extract their
    grain word at all.

    Bare singular unit nouns are now emitted as latent durations (matching
    duckling's production behavior — they're noun classifiers in real text,
    not durations), so this test opts into latent to verify the boundary fix
    still lets the token form for downstream composition rules.
    """
    text = "مسابقه تحدي الدقيقه"
    result = parse(text, ctx_ar, Options(with_latent=True), dims=("duration",))
    bodies = {(e.dim, e.body) for e in result}
    assert ("duration", "دقيقه") in bodies, (
        f"expected duration 'دقيقه'; got {sorted(bodies)!r}"
    )
    # And by default — without latent — the bare singular must not surface.
    assert parse(text, ctx_ar, Options(), dims=("duration",)) == []


@pytest.mark.parametrize(
    "text, allowed_bodies",
    [
        # AR `<n> $ → USD` previously skipped through `\n` between number
        # and `$`, producing a bogus `1\n$` span. Duckling treats `\n`
        # as a hard token boundary.
        ("1\n$", ()),
        ("$\n1", ()),
        # Compound input from production fuzz set: `1،$1\n$1` should
        # produce two `$1` tokens (or none), never `1\n$`.
        ("1،$1\n$1", ("$1",)),
        # AR currency word across newline must not bind.
        ("1\nدولار", ()),
    ],
)
def test_ar_money_does_not_cross_newline(ctx_ar, text, allowed_bodies):
    """Engine `_skip_whitespace` previously skipped `\\n` between pattern
    items, letting `<n> $`/`$ <n>`/`<n> <currency-word>` rules join tokens
    across linebreaks. Duckling treats `\\n` as a hard separator (it skips
    `\\t` but not `\\n`). This guards the engine fix.
    """
    result = parse(text, ctx_ar, Options(), dims=("amount_of_money",))
    bodies = [e.body for e in result]
    for body in bodies:
        assert "\n" not in body, (
            f"money span crossed newline: {bodies!r} for {text!r}"
        )
        assert body in allowed_bodies or not allowed_bodies, (
            f"unexpected body {body!r} for {text!r}; allowed: {allowed_bodies!r}"
        )


@pytest.mark.parametrize(
    "text, expected_value, expected_currency, expected_body",
    [
        # `و` separated by space, two-digit cents.
        ("1 دولار و 25", 1.25, "USD", "1 دولار و 25"),
        # `و` with no space (proclitic attachment), short tail.
        ("1 دولار و4", 1.04, "USD", "1 دولار و4"),
        # No space, two-digit cents.
        ("20 اورو و20", 20.2, "EUR", "20 اورو و20"),
        # Space variant for EUR.
        ("20 يورو و 20", 20.2, "EUR", "20 يورو و 20"),
        # Three-digit tail — Duckling still divides by 100, yielding > base.
        ("$1 و 250", 3.5, "USD", "$1 و 250"),
        # Comma-terminated — span must cut at `،` and not absorb the
        # following Arabic word.
        ("1 دولار و4،ساعة", 1.04, "USD", "1 دولار و4"),
    ],
)
def test_ar_money_intersect_with_waw_conjunction(
    ctx_ar, text, expected_value, expected_currency, expected_body
):
    """`<amount> و <number>` must compose like Duckling's intersect-with-cents:
    the trailing bare number is treated as cents (n/100 added). Mirrors EN
    `intersect (and number)` (`$20 and 43` → 20.43). Without this rule,
    `1 دولار و4` truncates to `1 دولار` and the `و4` tail is dropped.
    """
    result = parse(text, ctx_ar, Options(), dims=("amount_of_money",))
    bodies = [(e.body, getattr(e.value, "value", None), getattr(e.value, "currency", None)) for e in result]
    assert (expected_body, expected_value, expected_currency) in bodies, (
        f"expected {(expected_body, expected_value, expected_currency)!r} in {bodies!r}"
    )


def test_hour_word_does_not_match_inside_ordinal(ctx_en):
    """`yesterday fourth` must not produce a time span that eats `four` from
    `fourth`. Pre-fix, the `<word-H> (latent hour)` regex
    `one|two|...|twelve` lacked `\\b` anchors, so the engine's single-regex
    `finditer` path matched `four` inside `fourth`, the `<time> <tod>`
    combinator chained it onto `yesterday`, and the resulting spurious
    `yesterday four` token outranked plain `yesterday`.
    """
    result = parse("yesterday fourth", ctx_en, Options(), dims=("time", "ordinal"))
    time_bodies = {e.body for e in result if e.dim == "time"}
    assert "yesterday four" not in time_bodies, (
        f"time leaked into 'fourth': {[(e.dim, e.body) for e in result]!r}"
    )
