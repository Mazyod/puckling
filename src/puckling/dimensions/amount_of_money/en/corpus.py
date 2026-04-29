"""AmountOfMoney/EN/Corpus.hs — Python port (subset).

Limited to phrases that don't depend on a textual numeral parser, since the
Numeral dimension's English rules are not in place yet. Word-spelled numbers
(e.g. "ten dollars", "twenty euros") are intentionally omitted.

Upstream:
    https://raw.githubusercontent.com/facebook/duckling/main/Duckling/AmountOfMoney/EN/Corpus.hs
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    examples(
        {"value": 1, "unit": "USD", "type": "value"},
        ["$1"],
    ),
    examples(
        {"value": 10, "unit": "USD", "type": "value"},
        ["$10", "$ 10", "10$", "US$10", "10 dollars", "10 dollar"],
    ),
    examples(
        {"value": 10, "unit": "cent", "type": "value"},
        ["10 cent", "10 cents", "10 c", "10¢"],
    ),
    examples(
        {"value": 3.14, "unit": "USD", "type": "value"},
        ["USD3.14", "USD 3.14", "3.14 USD"],
    ),
    examples(
        {"value": 20, "unit": "EUR", "type": "value"},
        ["20€", "€20", "20 euros", "20 euro", "EUR 20", "EUR 20.0"],
    ),
    examples(
        {"value": 10, "unit": "GBP", "type": "value"},
        ["£10", "10 pounds", "GBP 10"],
    ),
    examples(
        {"value": 20, "unit": "INR", "type": "value"},
        ["20 Rupees", "20Rs", "Rs 20"],
    ),
    examples(
        {"value": 50, "unit": "USD", "type": "value"},
        ["$50", "50 dollars", "USD 50"],
    ),
    examples(
        {"value": 42, "unit": "KWD", "type": "value"},
        ["42 KWD", "KWD 42"],
    ),
    examples(
        {"value": 42, "unit": "SAR", "type": "value"},
        ["42 SAR", "SAR 42"],
    ),
    examples(
        {"value": 42, "unit": "AED", "type": "value"},
        ["42 AED", "AED 42"],
    ),
    examples(
        {"value": 100, "unit": "JPY", "type": "value"},
        ["100 yen", "¥100", "JPY 100"],
    ),
    examples(
        {"value": 20.43, "unit": "USD", "type": "value"},
        ["$20 and 43c", "$20 43c"],
    ),
)
