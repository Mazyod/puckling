"""Arabic Duration corpus — port of Duckling's Duration/AR/Corpus.hs."""

from __future__ import annotations

from puckling.corpus import Example, examples


def _value(value: int, unit: str, normalized_seconds: int) -> dict:
    return {
        "value": value,
        "unit": unit,
        "type": "value",
        "normalized": {"value": normalized_seconds, "unit": "second"},
    }


CORPUS: tuple[Example, ...] = (
    examples(
        _value(1, "second", 1),
        ["ثانية", "لحظة"],
    ),
    examples(
        _value(2, "minute", 120),
        ["دقيقتان", "دقيقتين"],
    ),
    examples(
        _value(5, "hour", 5 * 3600),
        ["خمسة ساعات"],
    ),
    examples(
        _value(30, "day", 30 * 86_400),
        ["30 يوم"],
    ),
    examples(
        _value(1, "week", 604_800),
        ["اسبوع"],
    ),
    examples(
        _value(7, "week", 7 * 604_800),
        ["سبع اسابيع"],
    ),
    examples(
        _value(1, "month", 2_592_000),
        ["شهر"],
    ),
    examples(
        _value(2, "month", 2 * 2_592_000),
        ["شهرين"],
    ),
    examples(
        _value(2, "year", 2 * 31_536_000),
        ["سنتين", "سنتان", "عامين", "عامان"],
    ),
)
