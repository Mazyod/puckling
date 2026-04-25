"""Arabic AmountOfMoney corpus.

Trimmed translation of `Duckling/AmountOfMoney/AR/Corpus.hs` — keeps only
phrases supported by the minimal Arabic ruleset (digit numerals + common
currency words). Word-form numerals (e.g. "عشرة دولارات") and intervals
("من 10 إلى 20 دولار") are intentionally out of scope for this unit.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    examples(
        {"value": 1, "unit": "USD", "type": "value"},
        ["$1", "1 دولار"],
    ),
    examples(
        {"value": 10, "unit": "USD", "type": "value"},
        ["$10", "$ 10", "10 $", "10$", "10 دولار"],
    ),
    examples(
        {"value": 20, "unit": "EUR", "type": "value"},
        ["20 يورو", "20 اورو", "20 أورو", "20€", "20 €"],
    ),
    examples(
        {"value": 10, "unit": "Pound", "type": "value"},
        ["10 جنيه", "10 جنيهات"],
    ),
    examples(
        {"value": 3, "unit": "GBP", "type": "value"},
        ["3 جنيهات استرلينية", "3 جنيه استرليني"],
    ),
    examples(
        {"value": 42, "unit": "KWD", "type": "value"},
        ["42 KWD", "42 دينار كويتي", "٤٢ دينار كويتي"],
    ),
    examples(
        {"value": 50, "unit": "Dinar", "type": "value"},
        ["٥٠ دينار", "50 دينار"],
    ),
    examples(
        {"value": 42, "unit": "LBP", "type": "value"},
        ["42 LBP", "42 ليرة لبنانية", "42 ليرات لبنانية"],
    ),
    examples(
        {"value": 42, "unit": "EGP", "type": "value"},
        ["42 EGP", "42 جنيه مصري", "42 جنيهات مصريه", "42 ج.م", "42 ج.م."],
    ),
    examples(
        {"value": 42, "unit": "QAR", "type": "value"},
        ["42 QAR", "42 ريال قطري", "42 ريالات قطرية"],
    ),
    examples(
        {"value": 42, "unit": "SAR", "type": "value"},
        ["42 SAR", "42 ريال سعودي"],
    ),
    examples(
        {"value": 5, "unit": "JOD", "type": "value"},
        ["5 دينار اردني", "5 دنانير أردنية"],
    ),
    examples(
        {"value": 100, "unit": "AED", "type": "value"},
        ["100 درهم إماراتي", "100 درهم اماراتي", "100 AED"],
    ),
)
