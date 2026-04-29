"""Corpus examples for Quantity EN.

Subset of upstream Duckling/Quantity/EN/Corpus.hs — restricted to phrases
this port currently handles (numeral + unit, optional "of <product>", and
"a/an <unit>"). Interval, precision-modifier, and kg<->g conversion
phrases are out-of-scope and tracked as TODOs in rules.py.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    examples(
        {"value": 2.0, "unit": "cup", "type": "value"},
        ["2 cups"],
    ),
    examples(
        {"value": 1.0, "unit": "cup", "type": "value"},
        ["1 cup", "a cup"],
    ),
    examples(
        {"value": 3.0, "unit": "cup", "type": "value", "product": "sugar"},
        ["3 Cups of sugar", "3 cups of sugar"],
    ),
    examples(
        {"value": 0.75, "unit": "cup", "type": "value"},
        ["0.75 cup", ".75 cups"],
    ),
    examples(
        {"value": 2.0, "unit": "gram", "type": "value"},
        ["2 grams", "2 g", "2 g.", "2 gs"],
    ),
    examples(
        {"value": 1.0, "unit": "gram", "type": "value"},
        ["a gram"],
    ),
    examples(
        {"value": 500.0, "unit": "gram", "type": "value", "product": "strawberries"},
        ["500 grams of strawberries"],
    ),
    examples(
        {"value": 1.0, "unit": "pound", "type": "value"},
        ["a Pound", "1 lb", "a lb"],
    ),
    examples(
        {"value": 2.0, "unit": "pound", "type": "value"},
        ["2 lbs", "2 pounds"],
    ),
    examples(
        {"value": 2.0, "unit": "pound", "type": "value", "product": "meat"},
        ["2 pounds of meat"],
    ),
    examples(
        {"value": 2.0, "unit": "ounce", "type": "value"},
        ["2 ounces", "2 oz"],
    ),
    examples(
        {"value": 1.0, "unit": "ounce", "type": "value"},
        ["an ounce", "1 oz", "an oz"],
    ),
    examples(
        {"value": 4.0, "unit": "ounce", "type": "value", "product": "chocolate"},
        ["4 ounces of chocolate"],
    ),
)
