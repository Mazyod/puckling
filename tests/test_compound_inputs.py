"""Compound-input tests — multiple dimensions in one phrase.

Fills a gap in upstream Duckling, which tests phrases in isolation but never
verifies that `parse("Email me at alice@example.com tomorrow at 5pm")` returns
three correctly-bounded entities at the right span offsets.

The seven case groups exercised here are:

1. Multiple dimensions in one phrase (EN + AR).
2. Adjacent same-dimension entities.
3. Greedy vs non-greedy disambiguation (longest match wins).
4. Entity range correctness (body slice + bounds + non-overlap).
5. Interleaved punctuation between same-dim entities.
6. Compound input with no entities.
7. Newline-separated lines.
"""

from __future__ import annotations

import pytest

from puckling import Entity, Options, parse

# ---------------------------------------------------------------------------
# helpers


def _dims_set(entities: list[Entity]) -> set[str]:
    return {e.dim for e in entities}


def _assert_spans_consistent(text: str, entities: list[Entity]) -> None:
    """Every entity's body must equal text[start:end] and stay within bounds."""
    for e in entities:
        assert e.start >= 0, f"negative start on {e!r}"
        assert e.end <= len(text), f"end past text on {e!r}"
        assert e.start < e.end, f"empty/inverted span on {e!r}"
        assert text[e.start : e.end] == e.body, (
            f"body/range mismatch: text[{e.start}:{e.end}]={text[e.start:e.end]!r} body={e.body!r}"
        )


def _assert_no_overlaps(entities: list[Entity]) -> None:
    """For any two entities a, b: either a.end <= b.start or b.end <= a.start."""
    spans = sorted([(e.start, e.end) for e in entities])
    for (s1, e1), (s2, e2) in zip(spans, spans[1:], strict=False):
        assert e1 <= s2, f"overlap: ({s1},{e1}) vs ({s2},{e2})"


# ---------------------------------------------------------------------------
# Group 1: multiple dimensions in one phrase (EN)


def test_email_time_money_in_one_phrase(ctx_en):
    text = "Email me at alice@example.io tomorrow at 5pm with $50"
    entities = parse(text, ctx_en, Options())
    dims = _dims_set(entities)
    assert {"email", "time", "amount_of_money"} <= dims
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


def test_url_and_money_in_one_phrase(ctx_en):
    text = "Visit https://example.com for $20 off"
    entities = parse(text, ctx_en, Options())
    dims = _dims_set(entities)
    assert {"url", "amount_of_money"} <= dims
    url = next(e for e in entities if e.dim == "url")
    money = next(e for e in entities if e.dim == "amount_of_money")
    assert url.body == "https://example.com"
    assert money.body == "$20"
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


def test_email_and_money_in_one_phrase(ctx_en):
    text = "My email is bob@test.org and the price is $100"
    entities = parse(text, ctx_en, Options())
    dims = _dims_set(entities)
    assert {"email", "amount_of_money"} <= dims
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


def test_distance_and_ordinal_in_one_phrase(ctx_en):
    text = "Send 5 km north then turn at the 3rd intersection"
    entities = parse(text, ctx_en, Options())
    dims = _dims_set(entities)
    # Expected: distance + ordinal/time, with no spurious money matches.
    assert "distance" in dims
    assert "amount_of_money" not in dims
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


@pytest.mark.xfail(
    reason=(
        "TODO(puckling): edge case — 'time' rule greedily consumes "
        "'55-1212 around 5pm' (length 18), beating phone_number "
        "'(415) 555-1212' (length 14) under longest-match selection. "
        "Real bug: phone_number tokens should win over partial time matches."
    ),
    strict=False,
)
def test_phone_number_with_trailing_time(ctx_en):
    text = "Call (415) 555-1212 around 5pm"
    entities = parse(text, ctx_en, Options())
    dims = _dims_set(entities)
    assert {"phone_number", "time"} <= dims


# ---------------------------------------------------------------------------
# Group 1b: multiple dimensions in one phrase (AR)


def test_arabic_call_with_day_and_time(ctx_ar):
    text = "اتصل بي يوم الجمعة الساعة 5 مساء"
    entities = parse(text, ctx_ar, Options())
    dims = _dims_set(entities)
    assert "time" in dims
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


def test_arabic_tomorrow_time_and_money(ctx_ar):
    text = "غدا الساعة 5 مساء سأرسل ٥٠ دينار"
    entities = parse(text, ctx_ar, Options())
    dims = _dims_set(entities)
    assert {"time", "amount_of_money"} <= dims
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


# ---------------------------------------------------------------------------
# Group 2: adjacent same-dimension entities


def test_two_adjacent_distance_entities(ctx_en):
    text = "5 km and 10 km are different"
    entities = parse(text, ctx_en, Options())
    distances = [e for e in entities if e.dim == "distance"]
    assert len(distances) == 2, f"expected 2 distances, got {distances!r}"
    bodies = sorted(e.body for e in distances)
    assert bodies == ["10 km", "5 km"]
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


def test_three_adjacent_money_entities(ctx_en):
    text = "$5 plus $10 equals $15"
    entities = parse(text, ctx_en, Options())
    monies = [e for e in entities if e.dim == "amount_of_money"]
    bodies = sorted(e.body for e in monies)
    assert bodies == ["$10", "$15", "$5"]
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


def test_two_adjacent_money_entities_unambiguous(ctx_en):
    """Two adjacent dollar amounts should both surface as money entities."""
    text = "$10 and $20"
    entities = parse(text, ctx_en, Options())
    monies = [e for e in entities if e.dim == "amount_of_money"]
    assert len(monies) == 2
    bodies = sorted(e.body for e in monies)
    assert bodies == ["$10", "$20"]
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


def test_two_adjacent_money_entities_with_separator(ctx_en):
    """Money pair without trailing letters that risk forming a time/temp span."""
    text = "$50, $75"
    entities = parse(text, ctx_en, Options())
    monies = [e for e in entities if e.dim == "amount_of_money"]
    assert len(monies) == 2
    bodies = sorted(e.body for e in monies)
    assert bodies == ["$50", "$75"]
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


def test_three_money_entities_with_separator(ctx_en):
    """Three money entities, comma-separated, all surface."""
    text = "I have $50, $75, $100"
    entities = parse(text, ctx_en, Options())
    monies = [e for e in entities if e.dim == "amount_of_money"]
    bodies = sorted(e.body for e in monies)
    assert bodies == ["$100", "$50", "$75"]
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


def test_pm_to_pm_is_single_interval(ctx_en):
    """An interval like '5pm to 7pm' surfaces as ONE time entity, not two."""
    text = "5pm to 7pm"
    entities = parse(text, ctx_en, Options())
    times = [e for e in entities if e.dim == "time"]
    assert len(times) == 1, f"expected single interval, got {times!r}"
    assert times[0].body == "5pm to 7pm"
    _assert_spans_consistent(text, entities)


# ---------------------------------------------------------------------------
# Group 3: greedy vs non-greedy disambiguation (longest match wins)


def test_distance_wins_over_bare_numeral(ctx_en):
    text = "5 km"
    entities = parse(text, ctx_en, Options())
    assert len(entities) == 1
    assert entities[0].dim == "distance"
    assert entities[0].body == "5 km"


def test_money_wins_over_bare_numeral(ctx_en):
    text = "$50"
    entities = parse(text, ctx_en, Options())
    assert len(entities) == 1
    assert entities[0].dim == "amount_of_money"
    assert entities[0].body == "$50"


def test_duration_wins_over_bare_numeral(ctx_en):
    text = "3 hours"
    entities = parse(text, ctx_en, Options())
    assert len(entities) == 1
    assert entities[0].dim == "duration"
    assert entities[0].body == "3 hours"


def test_ordinal_wins_over_bare_numeral(ctx_en):
    """'3rd' should surface as ordinal, not numeral '3'."""
    text = "my 3rd choice"
    entities = parse(text, ctx_en, Options())
    ordinals = [e for e in entities if e.dim == "ordinal"]
    assert ordinals, f"no ordinal in {entities!r}"
    assert ordinals[0].body == "3rd"
    numerals = [e for e in entities if e.dim == "numeral" and e.body == "3"]
    assert not numerals, f"bare numeral '3' should not appear: {numerals!r}"


# ---------------------------------------------------------------------------
# Group 4: entity range correctness


@pytest.mark.parametrize(
    "text",
    [
        "Email me at alice@example.io tomorrow at 5pm with $50",
        "Visit https://example.com for $20 off",
        "5 km and 10 km are different",
        "5km, 10km, and 15km",
        "tomorrow at 5pm",
        "$50",
        "alice@example.com\n5pm tomorrow",
    ],
)
def test_range_correctness_invariants(text, ctx_en):
    entities = parse(text, ctx_en, Options())
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


def test_no_overlap_invariant_compound(ctx_en):
    text = "Tomorrow at 5pm I owe alice@example.com $50"
    entities = parse(text, ctx_en, Options())
    _assert_no_overlaps(entities)
    _assert_spans_consistent(text, entities)
    dims = _dims_set(entities)
    assert {"time", "email", "amount_of_money"} <= dims


def test_arabic_range_correctness(ctx_ar):
    text = "غدا الساعة 5 مساء سأرسل ٥٠ دينار"
    entities = parse(text, ctx_ar, Options())
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


# ---------------------------------------------------------------------------
# Group 5: interleaved punctuation


def test_three_distances_with_commas_and_and(ctx_en):
    text = "5km, 10km, and 15km"
    entities = parse(text, ctx_en, Options())
    distances = [e for e in entities if e.dim == "distance"]
    bodies = sorted(e.body for e in distances)
    assert bodies == ["10km", "15km", "5km"]
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


def test_three_distances_have_correct_offsets(ctx_en):
    text = "5km, 10km, and 15km"
    entities = parse(text, ctx_en, Options())
    distances = sorted(
        (e for e in entities if e.dim == "distance"), key=lambda e: e.start
    )
    assert [(d.start, d.end) for d in distances] == [(0, 3), (5, 9), (15, 19)]


# ---------------------------------------------------------------------------
# Group 6: compound input with no entities


def test_no_entities_for_plain_prose(ctx_en):
    assert parse("hello world", ctx_en, Options()) == []


def test_no_entities_for_empty_string(ctx_en):
    assert parse("", ctx_en, Options()) == []


def test_no_entities_for_arabic_prose(ctx_ar):
    assert parse("مرحبا بالعالم", ctx_ar, Options()) == []


# ---------------------------------------------------------------------------
# Group 7: newline-separated lines


def test_newline_separated_email_then_time(ctx_en):
    text = "alice@example.com\n5pm tomorrow"
    entities = parse(text, ctx_en, Options())
    dims = _dims_set(entities)
    assert {"email", "time"} <= dims
    email = next(e for e in entities if e.dim == "email")
    time_ent = next(e for e in entities if e.dim == "time")
    assert email.body == "alice@example.com"
    assert email.start == 0
    assert email.end == 17  # immediately before the '\n'
    assert time_ent.start == 18  # immediately after the '\n'
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


def test_newline_separated_three_lines(ctx_en):
    text = "5 km\n$50\n3 hours"
    entities = parse(text, ctx_en, Options())
    dims = _dims_set(entities)
    assert {"distance", "amount_of_money", "duration"} <= dims
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)


def test_newline_does_not_merge_adjacent_dimensions(ctx_en):
    """A distance on one line and a money on the next must remain two entities."""
    text = "5 km\n$50"
    entities = parse(text, ctx_en, Options())
    assert len(entities) == 2
    by_dim = {e.dim: e for e in entities}
    assert by_dim["distance"].body == "5 km"
    assert by_dim["amount_of_money"].body == "$50"
    _assert_spans_consistent(text, entities)
    _assert_no_overlaps(entities)
