"""English Temperature corpus — port of Duckling/Temperature/EN/Corpus.hs.

Phrases that depend on a word-numeral parser ("thirty seven celsius",
"seventy Fahrenheit", ...) are intentionally omitted: this unit ships only
the small numeric seed rule and word-numeral support is provided by the
Numeral dimension's own EN rules. The phrase "- 2 degrees" is also omitted
because parsing a literal "minus" sign separated from the digits depends on
the Numeral parser too.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

# Each expected value matches exactly what ``parse(...)`` surfaces — i.e. the
# dict produced by the value class's ``resolve(context)``.

CORPUS: tuple[Example, ...] = (
    examples(
        {"value": 37, "unit": "celsius", "type": "value"},
        ["37°C", "37 ° celsius", "37 degrees Celsius"],
    ),
    examples(
        {"value": 70, "unit": "fahrenheit", "type": "value"},
        ["70°F", "70 ° Fahrenheit", "70 degrees F"],
    ),
    examples(
        {"value": 98.6, "unit": "fahrenheit", "type": "value"},
        ["98.6°F", "98.6 ° Fahrenheit", "98.6 degrees F"],
    ),
    examples(
        {"value": 45, "unit": "degree", "type": "value"},
        ["45°", "45 degrees", "45 deg."],
    ),
    examples(
        {"value": -2, "unit": "degree", "type": "value"},
        ["-2°", "2 degrees below zero", "2 below zero"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": 30, "unit": "degree"},
            "to": {"value": 40, "unit": "degree"},
        },
        ["between 30 and 40 degrees", "from 30 degrees to 40 degrees"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": 30, "unit": "celsius"},
            "to": {"value": 40, "unit": "celsius"},
        },
        [
            "between 30 and 40 celsius",
            "from 30 celsius and 40 celsius",
            "between 30 and 40 degrees celsius",
            "from 30 degrees celsius to 40 degrees celsius",
            "30-40 degrees celsius",
        ],
    ),
    examples(
        {"type": "interval", "from": {"value": 40, "unit": "degree"}},
        ["over 40 degrees", "at least 40 degrees", "more than 40 degrees"],
    ),
    examples(
        {"type": "interval", "to": {"value": 40, "unit": "degree"}},
        ["under 40 degrees", "less than 40 degrees", "lower than 40 degrees"],
    ),
)
