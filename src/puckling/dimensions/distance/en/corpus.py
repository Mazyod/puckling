"""Distance EN corpus — port of `Duckling/Distance/EN/Corpus.hs`.

Only examples that fit the foundation `DistanceValue` shape (`value` + `unit`)
and the digit-only numeric seed in `rules.py` are included. Entries needing
Numeral EN word numbers (e.g. "eight mile"), the ambiguous "M" unit, or
interval/min/max-shaped distance values from upstream are omitted here and
covered as TODOs for follow-up workers.
"""

from __future__ import annotations

from puckling.corpus import Example, examples


def _value(value: float | int, unit: str) -> dict:
    return {"value": value, "unit": unit, "type": "value"}


CORPUS: tuple[Example, ...] = (
    examples(
        _value(3, "kilometre"),
        ["3 kilometers", "3 km", "3km", "3k", "3.0 km"],
    ),
    examples(
        _value(8, "mile"),
        ["8 miles", "8 mi"],
        # TODO(puckling): edge case — "eight mile" needs Numeral EN word numbers.
    ),
    examples(
        _value(2, "centimetre"),
        ["2cm", "2 centimeters"],
    ),
    examples(
        _value(5, "inch"),
        ["5 in", "5''", '5"'],
        # TODO(puckling): edge case — "five inches" needs Numeral EN word numbers.
    ),
    examples(
        _value(1.87, "metre"),
        ["1.87 meters"],
    ),
    # Composite values:
    examples(
        _value(94, "inch"),
        ["7 feet and 10 inches", "7 feet, 10 inches", "7 feet 10 inches"],
    ),
    examples(
        _value(2001, "metre"),
        ["2 km and 1 meter", "2 kilometer, 1 metre", "2 kilometer 1 metre"],
    ),
    examples(
        _value(166, "inch"),
        ["2 yards 7 ft 10 inches", "2 yds, 7 feet and 10 inches", "2 yards, 7 feet, 10 in"],
    ),
    examples(
        _value(13, "foot"),
        ["2 yards and 7 feet", "2 yards, 7 feet", "2 yd 7'"],
    ),
    examples(
        _value(1000806, "centimetre"),
        [
            "10 kms 8 metres 6 cm",
            "10 kms, 8 meters, 6 cm",
            "10 kms, 8 meters and 6 centimeters",
        ],
    ),
    examples(
        _value(1.3048, "metre"),
        ["1 meter and 1 foot"],
    ),
    examples(
        _value(2.609344, "kilometre"),
        ["1 kilometer and 1 mile"],
    ),
    # TODO(puckling): edge case — ambiguous "M" unit (3m / 9m) not modelled in
    # the foundation `DistanceUnit` enum.
    # TODO(puckling): edge case — interval / under / over shapes from upstream
    # ("between 3 and 5 kilometers", "under 3.5 miles", "more than five inches",
    # etc.) require a richer DistanceValue (min/max).
)
