"""Arabic quantity corpus — ported from Duckling/Quantity/AR/Corpus.hs."""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    examples(
        {"value": 2, "unit": "gram", "type": "value"},
        [
            "2 غرام",
            "2 جرام",
            "0.002 كيلوغرام",
            "0.002 كيلوجرام",
            "2/1000 كغ",
            "2000 ملغ",
            "2000 ملج",
        ],
    ),
    examples(
        {"value": 1000, "unit": "gram", "type": "value"},
        [
            "كغ",
            "كيلوغرام",
            "كيلوجرام",
        ],
    ),
    examples(
        {"value": 2, "unit": "ounce", "type": "value"},
        [
            "2 اونصة",
            "أونصتان",
            "اونصتين",
        ],
    ),
    examples(
        {"value": 0.75, "unit": "cup", "type": "value"},
        [
            "3/4 كوب",
            "0.75 كوب",
            ".75 كوب",
        ],
    ),
    examples(
        {"value": 3, "unit": "ounce", "product": "الذهب", "type": "value"},
        [
            # TODO(puckling): edge case — "ثلاثة" requires the AR Numeral
            # word-form rules; for now we cover the digit form only.
            "3 اونصات من الذهب",
        ],
    ),
    examples(
        {"value": 3, "unit": "cup", "product": "السكر", "type": "value"},
        [
            "3 اكواب من السكر",
        ],
    ),
    examples(
        {"value": 500, "unit": "gram", "product": "الفراولة", "type": "value"},
        [
            "500 غرام من الفراولة",
            "500 غم من الفراولة",
            "500 جرام من الفراولة",
            "500 جم من الفراولة",
            "0.5 كيلوجرام من الفراولة",
            "0.5 كيلوغرام من الفراولة",
            "0.5 كغ من الفراولة",
            "500000 ملغ من الفراولة",
        ],
    ),
)
