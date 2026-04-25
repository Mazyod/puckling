"""Boundary-condition tests for puckling's public API.

Fills a real gap in upstream Duckling, which has no tests for empty input,
whitespace-only input, very long input, mixed-script input, or Unicode
confusables. Each test either pins an exact value or asserts the parser
"must not raise + must complete within the per-test timeout".
"""

from __future__ import annotations

import time
import unicodedata

import pytest

from puckling import Options, parse

# A ~10K character string of repeated English filler. Reused by every long-
# input test; building it once keeps each test body focused on its assertion.
_LONG_TEXT_EN = ("the quick brown fox jumps over the lazy dog. " * 222)[:10000]


# ---------------------------------------------------------------------------
# 1. Empty input


def test_empty_input_en(ctx_en):
    assert parse("", ctx_en, Options()) == []


def test_empty_input_ar(ctx_ar):
    assert parse("", ctx_ar, Options()) == []


# ---------------------------------------------------------------------------
# 2. Whitespace-only input


@pytest.mark.parametrize("text", ["   ", "\t", "\n\n", " \t\n ", "\r", "\v", "\f"])
def test_whitespace_only_en(ctx_en, text):
    assert parse(text, ctx_en, Options()) == [], f"unexpected entities for {text!r}"


@pytest.mark.parametrize("text", ["   ", "\t", "\n\n"])
def test_whitespace_only_ar(ctx_ar, text):
    assert parse(text, ctx_ar, Options()) == [], f"unexpected entities for {text!r}"


# ---------------------------------------------------------------------------
# 3. Single character


def test_single_char_letter_a_en(ctx_en):
    # English numeral rules treat the indefinite article "a" as 1
    # (e.g. "a dozen", "a couple"). Pinning the surfaced behavior here.
    entities = parse("a", ctx_en, Options())
    assert len(entities) == 1
    assert entities[0].dim == "numeral"
    assert entities[0].value == {"value": 1, "type": "value"}


def test_single_char_letter_a_ar(ctx_ar):
    # Arabic has no rule mapping the Latin "a" to anything.
    assert parse("a", ctx_ar, Options()) == []


def test_single_char_digit_en(ctx_en):
    entities = parse("5", ctx_en, Options())
    assert len(entities) == 1
    assert entities[0].dim == "numeral"
    assert entities[0].value == {"value": 5, "type": "value"}
    assert entities[0].body == "5"


def test_single_char_digit_ar(ctx_ar):
    entities = parse("5", ctx_ar, Options())
    assert len(entities) == 1
    assert entities[0].dim == "numeral"
    # AR numeral rules surface the value as a float.
    assert entities[0].value == {"value": 5.0, "type": "value"}


def test_single_char_space(ctx_en):
    assert parse(" ", ctx_en, Options()) == []


# ---------------------------------------------------------------------------
# 4. Very long input
#
# The unfiltered parser scales super-linearly on long English-like inputs
# (~10K chars of "fox jumps" filler clocks ~7s locally, blowing past the
# 3s spec boundary). The slow test asserts the spec target via wall-clock
# rather than `@pytest.mark.timeout(3)` because pytest-timeout's default
# thread method calls `os._exit(1)`, which is uncatchable by xfail. The
# session-level 5s timeout is also disabled here for the same reason.
# Sibling tests pin the fast path: dim-filtered EN, and AR (whose grammar
# happens to skip cheaply over Latin filler).


def test_very_long_input_does_not_hang(ctx_en):
    """Long full-grammar parses complete within the engine's wall-clock budget.

    Before `parse_timeout_ms` was introduced, this took ~7s on a 10K-char input
    because token saturation dominated. The engine now bails at its budget
    (default 2000 ms) and returns whatever it has, so this consistently finishes
    in well under 3 s. If a regression slows the budget enforcement, this test
    catches it.
    """
    started = time.monotonic()
    parse(_LONG_TEXT_EN, ctx_en, Options())
    elapsed = time.monotonic() - started
    assert elapsed < 3.0, f"parse of 10K-char string took {elapsed:.2f}s, want < 3s"


@pytest.mark.timeout(3)
def test_very_long_input_with_dim_filter(ctx_en):
    """Realistic long-input path: callers filter to the dimension they want."""
    parse(_LONG_TEXT_EN, ctx_en, Options(), dims=("numeral",))


@pytest.mark.timeout(3)
def test_very_long_input_arabic(ctx_ar):
    parse(_LONG_TEXT_EN, ctx_ar, Options())


# ---------------------------------------------------------------------------
# 5. Mixed-script input (Arabic + English)


def test_mixed_script_en(ctx_en):
    # Under EN the English clock rule fires; the Arabic word is ignored.
    entities = parse("غدا at 5pm", ctx_en, Options())
    assert any(e.dim == "time" and e.body == "at 5pm" for e in entities), (
        f"expected an 'at 5pm' time entity, got {entities!r}"
    )


def test_mixed_script_ar(ctx_ar):
    # Under AR the Arabic "غدا" (tomorrow) parses; "5" is a bare numeral.
    entities = parse("غدا at 5pm", ctx_ar, Options())
    dims = {e.dim for e in entities}
    bodies = {e.body for e in entities}
    # Must not crash and must surface the Arabic time entity.
    assert "time" in dims
    assert "غدا" in bodies


# ---------------------------------------------------------------------------
# 6. Unicode confusables / digit forms


# Each of these "5"-glyphs folds through the regex engine's UNICODE digit
# class today and surfaces a numeral. EN rules emit `int`, AR rules emit
# `float` — pinning the observed behavior locks the door on silent
# regressions in either locale's handling of non-ASCII digit shapes.
_DIGIT_FORMS = (
    pytest.param("٥", id="arabic-indic"),  # U+0665
    pytest.param("۵", id="persian-indic"),  # U+06F5
    pytest.param("５", id="fullwidth"),  # U+FF15
)


@pytest.mark.parametrize("text", _DIGIT_FORMS)
def test_alt_digit_form_en(ctx_en, text):
    entities = parse(text, ctx_en, Options())
    assert len(entities) == 1
    assert entities[0].dim == "numeral"
    assert entities[0].value == {"value": 5, "type": "value"}


@pytest.mark.parametrize("text", _DIGIT_FORMS)
def test_alt_digit_form_ar(ctx_ar, text):
    entities = parse(text, ctx_ar, Options())
    assert len(entities) == 1
    assert entities[0].dim == "numeral"
    assert entities[0].value == {"value": 5.0, "type": "value"}


# ---------------------------------------------------------------------------
# 7. Control characters


def test_control_chars_no_crash(ctx_en):
    # NUL + BEL between digit and unit. The parser must not crash; the
    # control bytes break the contiguous distance regex, so only the bare
    # numeral survives.
    entities = parse("5\x00\x07km", ctx_en, Options())
    assert any(e.dim == "numeral" and e.value == {"value": 5, "type": "value"} for e in entities)


def test_control_chars_at_boundary(ctx_en):
    # Leading/trailing/embedded NULs must not crash.
    for text in ("\x00", "\x005", "5\x00", "\x005\x00km"):
        parse(text, ctx_en, Options())


# ---------------------------------------------------------------------------
# 8. Combining marks / NFC vs NFD


def test_combining_marks_nfc(ctx_en):
    # Precomposed "é" (U+00E9). No rule matches; must not crash.
    text = "é"
    assert unicodedata.is_normalized("NFC", text)
    parse(text, ctx_en, Options())


def test_combining_marks_nfd(ctx_en):
    # Decomposed "é" (e + U+0301). No rule matches; must not crash.
    text = "é"
    assert unicodedata.is_normalized("NFD", text)
    parse(text, ctx_en, Options())


def test_combining_marks_inside_token(ctx_en):
    # NFD form embedded in a longer string — must not crash and must not
    # corrupt range tracking for any other entity surfaced.
    text = "café 5km"
    entities = parse(text, ctx_en, Options())
    for e in entities:
        # All ranges must be valid UTF-16-agnostic Python slice indices.
        assert 0 <= e.start <= e.end <= len(text)
        assert text[e.start : e.end] == e.body


# ---------------------------------------------------------------------------
# 9. RTL / LTR marks embedded in Arabic text


def test_rtl_mark_alone(ctx_ar):
    # U+200F by itself must not crash and produces nothing.
    assert parse("‏", ctx_ar, Options()) == []


def test_lrm_mark_alone(ctx_en):
    # U+200E by itself must not crash and produces nothing.
    assert parse("‎", ctx_en, Options()) == []


def test_rlm_inside_arabic(ctx_ar):
    # RLM right after "غدا" must not break the time-of-day match.
    entities = parse("غدا‏", ctx_ar, Options())
    assert any(e.dim == "time" and e.body == "غدا" for e in entities)


def test_lrm_inside_arabic(ctx_ar):
    # LRM right after "غدا" must not break the time-of-day match.
    entities = parse("غدا‎", ctx_ar, Options())
    assert any(e.dim == "time" and e.body == "غدا" for e in entities)


def test_directional_mark_between_digit_and_unit(ctx_en):
    # An RLM between "5" and "km" splits the distance match; only the
    # numeral survives. Must not crash.
    entities = parse("5‏km", ctx_en, Options())
    assert any(e.dim == "numeral" and e.value == {"value": 5, "type": "value"} for e in entities)


# ---------------------------------------------------------------------------
# 10. Very large numbers


def test_very_large_number_en(ctx_en):
    text = "9" * 18  # 999999999999999999
    entities = parse(text, ctx_en, Options())
    assert len(entities) == 1
    assert entities[0].dim == "numeral"
    # Python ints are arbitrary precision; the value must round-trip exactly.
    assert entities[0].value == {"value": int(text), "type": "value"}


def test_very_large_number_no_overflow(ctx_en):
    # 20-digit number — well past int64 — must still be exact under EN.
    text = "9" * 20
    entities = parse(text, ctx_en, Options())
    assert len(entities) == 1
    assert entities[0].value == {"value": int(text), "type": "value"}


# ---------------------------------------------------------------------------
# 11. Negative zero and sign edge cases


def test_negative_zero(ctx_en):
    entities = parse("-0", ctx_en, Options())
    assert len(entities) == 1
    # Pinned: -0 collapses to 0 (Python equality), body retains the sign.
    assert entities[0].dim == "numeral"
    assert entities[0].value == {"value": 0, "type": "value"}
    assert entities[0].body == "-0"


def test_explicit_positive_sign(ctx_en):
    # The leading "+" is not part of the numeral rule; only "5" matches.
    entities = parse("+5", ctx_en, Options())
    assert len(entities) == 1
    assert entities[0].value == {"value": 5, "type": "value"}
    assert entities[0].body == "5"
    assert entities[0].start == 1


def test_double_negative_sign_en(ctx_en):
    # The negative-numeral rule consumes one of the two minuses: "-5".
    entities = parse("--5", ctx_en, Options())
    assert len(entities) == 1
    assert entities[0].value == {"value": -5, "type": "value"}
    assert entities[0].body == "-5"
    assert entities[0].start == 1


# ---------------------------------------------------------------------------
# 12. Whitespace inside numbers


def test_space_before_thousands_separator(ctx_en):
    # "1 ,000" — the space breaks the integer-with-thousands rule, so the
    # parser sees two separate numerals.
    entities = parse("1 ,000", ctx_en, Options())
    values = sorted(e.value["value"] for e in entities if e.dim == "numeral")
    assert values == [0, 1]


def test_spaces_between_digits(ctx_en):
    # " 1 0 0" — each digit becomes its own numeral entity.
    entities = parse(" 1 0 0", ctx_en, Options())
    values = [e.value["value"] for e in entities if e.dim == "numeral"]
    assert values == [1, 0, 0]


# ---------------------------------------------------------------------------
# 13. Multiple consecutive spaces between tokens


def test_multiple_spaces_in_distance(ctx_en):
    # "5    km" should still parse as 5 km — Duckling's distance regex
    # tolerates run-on whitespace.
    entities = parse("5    km", ctx_en, Options())
    assert any(
        e.dim == "distance"
        and e.value == {"value": 5, "type": "value", "unit": "kilometre"}
        for e in entities
    )


def test_multiple_spaces_in_distance_in_sentence(ctx_en):
    entities = parse("I went 5    km today", ctx_en, Options())
    distances = [e for e in entities if e.dim == "distance"]
    assert distances, f"expected a distance entity, got {entities!r}"
    assert distances[0].value == {"value": 5, "type": "value", "unit": "kilometre"}
    assert distances[0].body == "5    km"


# ---------------------------------------------------------------------------
# 14. Trailing punctuation


def test_trailing_period_distance(ctx_en):
    entities = parse("5km.", ctx_en, Options())
    assert any(
        e.dim == "distance"
        and e.value == {"value": 5, "type": "value", "unit": "kilometre"}
        and e.body == "5km"
        for e in entities
    )


def test_trailing_comma_money(ctx_en):
    entities = parse("$50,", ctx_en, Options())
    assert any(
        e.dim == "amount_of_money"
        and e.value == {"type": "value", "value": 50, "unit": "USD"}
        and e.body == "$50"
        for e in entities
    )


def test_trailing_bang_email(ctx_en):
    entities = parse("alice@example.com!", ctx_en, Options())
    assert any(
        e.dim == "email"
        and e.value == {"value": "alice@example.com", "type": "value"}
        and e.body == "alice@example.com"
        for e in entities
    )
