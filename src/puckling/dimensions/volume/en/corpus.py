"""English Volume corpus — port of `Duckling/Volume/EN/Corpus.hs`.

Interval phrases (`between … and …`, `under`, `over`, `at most`, `more than`)
are intentionally omitted: the puckling `VolumeValue` dataclass cannot yet
express min/max/interval shapes.
"""

from __future__ import annotations

from puckling.corpus import Example, examples


def _v(value: float, unit: str) -> dict:
    return {"value": value, "unit": unit, "type": "value"}


CORPUS: tuple[Example, ...] = (
    examples(
        _v(1, "litre"),
        ["1 liter", "1 litre", "one liter", "a liter"],
    ),
    examples(
        _v(2, "litre"),
        ["2 liters", "2l"],
    ),
    examples(
        _v(1000, "litre"),
        ["1000 liters", "thousand liters"],
    ),
    examples(
        _v(0.5, "litre"),
        ["half liter", "half-litre", "half a liter"],
    ),
    examples(
        _v(0.25, "litre"),
        ["quarter-litre", "fourth of liter"],
    ),
    examples(
        _v(1, "millilitre"),
        ["one milliliter", "an ml", "a millilitre"],
    ),
    examples(
        _v(250, "millilitre"),
        ["250 milliliters", "250 millilitres", "250ml", "250mls", "250 ml"],
    ),
    examples(
        _v(3, "gallon"),
        ["3 gallons", "3 gal", "3gal", "around three gallons"],
    ),
    examples(
        _v(0.5, "gallon"),
        ["0.5 gals", "1/2 gallon", "half a gallon"],
    ),
    examples(
        _v(0.1, "gallon"),
        ["0.1 gallons", "tenth of a gallon"],
    ),
    examples(
        _v(3, "hectolitre"),
        ["3 hectoliters"],
    ),
    # TODO(puckling): edge case — interval/min/max corpus entries omitted
    # until VolumeValue can express min/max/interval state.
)
