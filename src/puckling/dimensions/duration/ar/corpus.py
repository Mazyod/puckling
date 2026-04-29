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
        _value(1, "hour", 3600),
        ["ساعة"],
    ),
    examples(
        _value(2, "hour", 2 * 3600),
        ["ساعتين", "ساعتان"],
    ),
    examples(
        _value(3, "hour", 3 * 3600),
        ["3 ساعات", "٣ ساعات", "ثلاث ساعات"],
    ),
    examples(
        _value(5, "hour", 5 * 3600),
        ["خمسة ساعات"],
    ),
    examples(
        _value(5, "minute", 5 * 60),
        ["5 دقائق", "خمس دقائق"],
    ),
    examples(
        _value(15, "minute", 15 * 60),
        ["ربع ساعة"],
    ),
    examples(
        _value(30, "minute", 30 * 60),
        ["نصف ساعة", "1/2 ساعة"],
    ),
    examples(
        _value(45, "minute", 45 * 60),
        ["3/4 ساعة", "ثلاثة أرباع ساعة"],
    ),
    examples(
        _value(90, "minute", 90 * 60),
        ["1.5 ساعة"],
    ),
    examples(
        _value(30, "day", 30 * 86_400),
        ["30 يوم"],
    ),
    examples(
        _value(2, "day", 2 * 86_400),
        ["يومين", "يومان"],
    ),
    examples(
        _value(1, "week", 604_800),
        ["اسبوع", "أسبوع"],
    ),
    examples(
        _value(2, "week", 2 * 604_800),
        ["اسبوعين", "أسبوعان"],
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
        ["شهرين", "شهران"],
    ),
    examples(
        _value(2, "year", 2 * 31_536_000),
        ["سنتين", "سنتان", "عامين", "عامان"],
    ),
)
