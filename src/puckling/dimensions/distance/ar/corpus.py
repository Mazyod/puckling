"""Corpus for distance / Arabic.

Modelled on `Duckling/Volume/AR/Corpus.hs` since upstream Duckling has no
`Distance/AR/Corpus.hs`. Phrases cover the metric (km, m, cm, mm) and imperial
(mile, yard, foot, inch) units that `DistanceUnit` exposes.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    examples(
        {"value": 5, "unit": "kilometre", "type": "value"},
        ["٥ كم", "5 كيلومتر", "5 كم", "٥ كيلو متر"],
    ),
    examples(
        {"value": 3, "unit": "metre", "type": "value"},
        ["3 متر", "٣ متر", "3 أمتار"],
    ),
    examples(
        {"value": 50, "unit": "centimetre", "type": "value"},
        ["50 سم", "٥٠ سنتيمتر", "50 سنتي متر"],
    ),
    examples(
        {"value": 250, "unit": "millimetre", "type": "value"},
        ["250 مم", "٢٥٠ ميليمتر", "250 مليمتر"],
    ),
    examples(
        {"value": 2, "unit": "mile", "type": "value"},
        ["2 ميل", "٢ ميل", "2 أميال"],
    ),
    examples(
        {"value": 4, "unit": "yard", "type": "value"},
        ["4 ياردة", "٤ ياردات"],
    ),
    examples(
        {"value": 6, "unit": "foot", "type": "value"},
        ["6 قدم", "٦ أقدام"],
    ),
    examples(
        {"value": 12, "unit": "inch", "type": "value"},
        ["12 بوصة", "١٢ إنش", "12 انش"],
    ),
)
