"""Arabic time corpus — supplemental examples for intervals + numeric dates.

Reference time: 2013-02-12T04:30:00 UTC, Tuesday. Each example carries the
expected `resolve()` dict, so tests can do a loose subset comparison (the same
pattern used by `corpus.py`).

Phrases are adapted from `Duckling/Time/AR/Corpus.hs`, scoped to forms that the
supplemental ruleset (`intervals_rules.py`) is responsible for.
"""

from __future__ import annotations

from puckling.corpus import Example, examples


def _instant(value: str, grain: str) -> dict:
    return {"value": value, "grain": grain}


def _interval(start: tuple[str, str], end: tuple[str, str]) -> dict:
    return {
        "type": "interval",
        "from": _instant(*start),
        "to": _instant(*end),
    }


def _open_to(value: str, grain: str) -> dict:
    return {"type": "interval", "to": _instant(value, grain)}


def _open_from(value: str, grain: str) -> dict:
    return {"type": "interval", "from": _instant(value, grain)}


CORPUS: tuple[Example, ...] = (
    # ----- Closed intervals: between X and Y -------------------------------
    examples(
        _interval(
            ("2013-02-13T00:00:00+00:00", "day"),
            ("2013-02-15T00:00:00+00:00", "day"),
        ),
        ["بين غدا و الجمعة", "بين الغد و الجمعة"],
    ),
    examples(
        _interval(
            ("2013-02-15T00:00:00+00:00", "day"),
            ("2013-02-18T00:00:00+00:00", "day"),
        ),
        ["بين الجمعة و الاثنين"],
    ),
    examples(
        _interval(
            ("2013-02-13T00:00:00+00:00", "day"),
            ("2013-02-14T00:00:00+00:00", "day"),
        ),
        ["بين غدا و بعد غد"],
    ),
    # ----- Closed intervals: from X to Y -----------------------------------
    examples(
        _interval(
            ("2013-02-13T00:00:00+00:00", "day"),
            ("2013-02-15T00:00:00+00:00", "day"),
        ),
        ["من غدا الى الجمعة", "من غدا إلى الجمعة", "من غدا حتى الجمعة"],
    ),
    examples(
        _interval(
            ("2013-02-12T15:00:00+00:00", "minute"),
            ("2013-02-12T17:30:00+00:00", "minute"),
        ),
        ["من 15:00 الى 17:30", "من 15:00 إلى 17:30"],
    ),
    # TODO(puckling): edge case — "من 4 ابريل الى 10 ابريل" needs interval
    # support but the foundation TimeData closures don't dedupe across
    # iterations, so two `<day> <month>` operands per input saturate the parse
    # forest. Left to a future engine/foundation pass.
    # NOTE: bare-dash intervals like "4 ابريل - 10 ابريل" are intentionally
    # omitted — without an explicit `بين`/`من` prefix the rule would consume
    # adjacent numerals and saturate the parse forest.
    # ----- Open intervals: until / before X --------------------------------
    examples(
        _open_to("2013-02-13T00:00:00+00:00", "day"),
        ["قبل غدا", "حتى غدا", "الى غدا", "إلى غدا"],
    ),
    examples(
        _open_to("2013-02-15T00:00:00+00:00", "day"),
        ["قبل الجمعة", "حتى الجمعة"],
    ),
    examples(
        _open_to("2013-02-12T18:00:00+00:00", "minute"),
        ["قبل 18:00", "حتى 18:00"],
    ),
    examples(
        _open_to("2013-04-04T00:00:00+00:00", "day"),
        ["قبل 4 ابريل", "حتى 4 ابريل"],
    ),
    # ----- Open intervals: after / since X ---------------------------------
    # NOTE: "بعد غدا" is intentionally omitted — the existing AR `بعد غد` rule
    # produces "day after tomorrow" (instant) on the same span, so the parser
    # disambiguator surfaces a different value than an open interval.
    examples(
        _open_from("2013-02-15T00:00:00+00:00", "day"),
        ["بعد الجمعة", "منذ الجمعة"],
    ),
    examples(
        _open_from("2013-02-12T18:00:00+00:00", "minute"),
        ["بعد 18:00", "منذ 18:00"],
    ),
    examples(
        _open_from("2013-04-04T00:00:00+00:00", "day"),
        ["منذ 4 ابريل"],
    ),
    # ----- DD/MM (current ref-year) ----------------------------------------
    examples(
        {"value": "2013-09-21T00:00:00+00:00", "grain": "day", "type": "value"},
        ["21/09", "21-09"],
    ),
    examples(
        {"value": "2013-04-04T00:00:00+00:00", "grain": "day", "type": "value"},
        ["04/04", "4/4"],
    ),
    examples(
        {"value": "2013-12-31T00:00:00+00:00", "grain": "day", "type": "value"},
        ["31/12", "31-12"],
    ),
    # ----- DD/MM/YYYY and DD-MM-YYYY ---------------------------------------
    examples(
        {"value": "2014-04-04T00:00:00+00:00", "grain": "day", "type": "value"},
        ["04/04/2014", "4-4-2014"],
    ),
    examples(
        {"value": "2013-09-21T00:00:00+00:00", "grain": "day", "type": "value"},
        ["21/09/2013", "21-09-2013"],
    ),
    examples(
        {"value": "1990-01-15T00:00:00+00:00", "grain": "day", "type": "value"},
        ["15-01-1990", "15/01/1990"],
    ),
    # ----- YYYY-MM-DD ------------------------------------------------------
    examples(
        {"value": "2013-04-04T00:00:00+00:00", "grain": "day", "type": "value"},
        ["2013-04-04"],
    ),
    examples(
        {"value": "1974-10-31T00:00:00+00:00", "grain": "day", "type": "value"},
        ["1974-10-31"],
    ),
    # ----- Ordinal-day-of-month + month ------------------------------------
    examples(
        {"value": "2013-04-04T00:00:00+00:00", "grain": "day", "type": "value"},
        ["الرابع من ابريل", "الرابع من نيسان"],
    ),
    examples(
        {"value": "2013-04-01T00:00:00+00:00", "grain": "day", "type": "value"},
        ["الأول من ابريل", "الاول من ابريل", "الأول من نيسان"],
    ),
    examples(
        {"value": "2013-03-01T00:00:00+00:00", "grain": "day", "type": "value"},
        ["الاول من مارس", "الأول من اذار", "الأول من آذار"],
    ),
    examples(
        {"value": "2013-02-13T00:00:00+00:00", "grain": "day", "type": "value"},
        ["الثالث عشر من شباط", "الثالث عشر من فبراير"],
    ),
    examples(
        {"value": "2013-04-05T00:00:00+00:00", "grain": "day", "type": "value"},
        ["الخامس من ابريل", "الخامس من نيسان"],
    ),
)
