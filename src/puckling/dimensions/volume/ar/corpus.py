"""Volume corpus for Arabic.

Ported from Duckling's ``Duckling/Volume/AR/Corpus.hs``.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    examples(
        {"value": 250, "unit": "millilitre", "type": "value"},
        ["250 مل", "250مل", "250 ميليلتر", "250 ملي لتر", "٢٥٠ مل", "٢٥٠مل"],
    ),
    examples(
        {"value": 2, "unit": "litre", "type": "value"},
        ["2 لتر", "٢ لتر", "٢لتر", "لتران", "لترين"],
    ),
    examples(
        {"value": 1.5, "unit": "litre", "type": "value"},
        ["1.5 لتر", "١٫٥ لتر"],
    ),
    examples(
        {"value": 3, "unit": "gallon", "type": "value"},
        ["3 غالون", "3 جالون", "3 غالونات", "3 جالونات", "٣ غالونات"],
    ),
    examples(
        {"value": 3, "unit": "hectolitre", "type": "value"},
        ["3 هكتوليتر", "3 هكتو ليتر", "٣ هكتوليتر"],
    ),
    examples(
        {"value": 0.5, "unit": "litre", "type": "value"},
        ["نصف لتر", "نص لتر"],
    ),
    examples(
        {"value": 0.25, "unit": "litre", "type": "value"},
        ["ربع لتر"],
    ),
    examples(
        {"value": 1.5, "unit": "litre", "type": "value"},
        ["لتر ونصف", "لتر و نص", "لتر و نصف", "لتر ونص"],
    ),
    examples(
        {"value": 1.25, "unit": "litre", "type": "value"},
        ["لتر وربع", "لتر و ربع"],
    ),
)
