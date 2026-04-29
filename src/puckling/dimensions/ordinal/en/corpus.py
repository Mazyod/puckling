"""English ordinal corpus.

Translated from Duckling's ``Duckling/Ordinal/EN/Corpus.hs``.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    examples({"value": 1, "type": "ordinal"}, ["first", "1st"]),
    examples({"value": 2, "type": "ordinal"}, ["second", "2nd"]),
    examples({"value": 3, "type": "ordinal"}, ["third", "3rd"]),
    examples({"value": 4, "type": "ordinal"}, ["fourth", "4th"]),
    examples({"value": 8, "type": "ordinal"}, ["eighth", "8th"]),
    examples({"value": 11, "type": "ordinal"}, ["eleventh", "11th"]),
    examples({"value": 12, "type": "ordinal"}, ["twelfth", "12th"]),
    examples({"value": 13, "type": "ordinal"}, ["thirteenth", "13th"]),
    examples(
        {"value": 25, "type": "ordinal"},
        [
            "twenty-fifth",
            "twenty—fifth",
            "twenty fifth",
            "twentyfifth",
            "25th",
        ],
    ),
    examples(
        {"value": 31, "type": "ordinal"},
        [
            "thirty-first",
            "thirty—first",
            "thirty first",
            "thirtyfirst",
            "31st",
        ],
    ),
    examples(
        {"value": 42, "type": "ordinal"},
        [
            "forty-second",
            "forty—second",
            "forty second",
            "fortysecond",
            "42nd",
        ],
    ),
    examples(
        {"value": 73, "type": "ordinal"},
        [
            "seventy-third",
            "seventy—third",
            "seventy third",
            "seventythird",
            "73rd",
        ],
    ),
    examples({"value": 90, "type": "ordinal"}, ["ninetieth", "90th"]),
)
