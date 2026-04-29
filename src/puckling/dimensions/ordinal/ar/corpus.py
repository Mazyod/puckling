"""Arabic ordinal corpus — ported from Duckling/Ordinal/AR/Corpus.hs."""

from __future__ import annotations

from puckling.corpus import Example, examples


def _ordinal(value: int) -> dict:
    return {"value": value, "type": "ordinal"}


CORPUS: tuple[Example, ...] = (
    examples(_ordinal(1), ["الاول", "الأول", "اول"]),
    examples(_ordinal(2), ["الثاني", "الثان", "ثاني"]),
    examples(_ordinal(3), ["الثالث", "ثالث"]),
    examples(_ordinal(4), ["الرابع", "رابع"]),
    examples(_ordinal(5), ["الخامس", "الخامسة"]),
    examples(_ordinal(7), ["السابع", "سابعة"]),
    examples(_ordinal(8), ["الثامن", "ثامن"]),
    examples(_ordinal(10), ["العاشر", "عاشرة"]),
    examples(_ordinal(11), ["الأحد عشر", "الإحدى عشرة", "الحادي عشرة"]),
    examples(_ordinal(12), ["الثاني عشرة", "الثان عشر", "الاثنى عشر"]),
    examples(_ordinal(13), ["الثالث عشر", "الثالثة عشرة"]),
    examples(_ordinal(14), ["الرابع عشر", "الرابعة عشرة"]),
    examples(_ordinal(20), ["العشرون", "العشرين"]),
    examples(_ordinal(21), ["الحادي والعشرين", "الواحد و العشرون"]),
    examples(_ordinal(25), ["الخامس والعشرين", "الخامس و العشرون"]),
    examples(_ordinal(31), ["الواحد والثلاثون", "الواحد والثلاثين"]),
    examples(_ordinal(38), ["الثامن والثلاثون", "الثامن و الثلاثين"]),
    examples(_ordinal(72), ["الثان والسبعون", "الثاني والسبعين"]),
    examples(_ordinal(90), ["التسعون", "التسعين"]),
)
