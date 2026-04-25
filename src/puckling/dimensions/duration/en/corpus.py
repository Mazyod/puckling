"""English Duration corpus — port of `Duckling/Duration/EN/Corpus.hs`.

Each entry's expected value is the dict produced by ``DurationValue.resolve``
(``{"value", "unit", "type", "normalized": {"value", "unit"}}``).
"""

from __future__ import annotations

from puckling.corpus import Example, examples

_SECONDS_PER_UNIT: dict[str, int] = {
    "second": 1,
    "minute": 60,
    "hour": 3_600,
    "day": 86_400,
    "week": 604_800,
    "month": 2_592_000,
    "quarter": 7_776_000,
    "year": 31_536_000,
}


def _v(value: int, unit: str) -> dict:
    return {
        "value": value,
        "unit": unit,
        "type": "value",
        "normalized": {
            "value": value * _SECONDS_PER_UNIT[unit],
            "unit": "second",
        },
    }


CORPUS: tuple[Example, ...] = (
    examples(_v(1, "second"), ["one sec", "1 second", '1"']),
    examples(
        _v(2, "minute"),
        [
            "2 mins",
            "two minutes",
            "2'",
            "2 more minutes",
            "two additional minutes",
            "2 extra minutes",
            "2 less minutes",
            "2 fewer minutes",
            "2m",
            "2 m",
        ],
    ),
    examples(_v(30, "day"), ["30 days"]),
    examples(_v(7, "week"), ["seven weeks"]),
    examples(_v(1, "month"), ["1 month", "a month"]),
    examples(_v(3, "quarter"), ["3 quarters"]),
    examples(_v(2, "year"), ["2 years"]),
    examples(
        _v(30, "minute"),
        ["half an hour", "half hour", "1/2 hour", "1/2h", "1/2 h"],
    ),
    examples(_v(12, "hour"), ["half a day", "half day", "1/2 day"]),
    examples(
        _v(90, "minute"),
        [
            "an hour and a half",
            "one hour and half",
            "1 hour thirty",
            "1 hour and thirty",
            "1.5 hours",
            "1.5 hrs",
            # TODO(puckling): edge case — needs full Numeral EN composition.
            # "one and two quarter hour",
            # "one and two quarters hour",
            # "one and two quarter of hour",
            # "one and two quarters of hour",
        ],
    ),
    examples(
        _v(75, "minute"),
        [
            "1 hour fifteen",
            "1 hour and fifteen",
            "one and quarter hour",
            "one and a quarter hour",
            "one and one quarter hour",
            "one and quarter of hour",
            "one and a quarter of hour",
            "one and one quarter of hour",
        ],
    ),
    examples(_v(130, "minute"), ["2 hours ten", "2 hour and 10"]),
    examples(
        _v(3615, "second"),
        ["1 hour fifteen seconds", "1 hour and fifteen seconds"],
    ),
    examples(_v(45, "day"), ["a month and a half", "one month and half"]),
    examples(
        _v(27, "month"),
        [
            "2 years and 3 months",
            "2 years, 3 months",
            "2 years 3 months",
        ],
    ),
    examples(
        _v(31_719_604, "second"),
        [
            "1 year, 2 days, 3 hours and 4 seconds",
            "1 year 2 days 3 hours and 4 seconds",
            # TODO(puckling): edge case — Oxford comma intentionally unsupported upstream.
        ],
    ),
    examples(
        _v(330, "second"),
        [
            "5 and a half minutes",
            "five and half min",
            "5 and an half minute",
        ],
    ),
    examples(
        _v(105, "minute"),
        [
            "one and three quarter hour",
            "one and three quarters hour",
            "one and three quarter of hour",
            "one and three quarters of hour",
            "one and three quarter of hours",
            "one and three quarters of hours",
            "an hour and 45 minutes",
            "one hour and 45 minutes",
        ],
    ),
    examples(
        _v(135, "minute"),
        [
            "two and quarter hour",
            "two and a quarter of hour",
            "two and quarter of hours",
            "two and a quarter of hours",
        ],
    ),
    examples(
        _v(90, "second"),
        ["a minute and 30 seconds", "one minute and 30 seconds"],
    ),
    examples(_v(3630, "second"), ["an hour and 30 seconds"]),
    examples(
        _v(930, "second"),
        ["15.5 minutes", "15.5 minute", "15.5 mins", "15.5 min"],
    ),
)
