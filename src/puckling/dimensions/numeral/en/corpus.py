"""English Numeral corpus — ported from `Duckling/Numeral/EN/Corpus.hs`."""

from __future__ import annotations

from puckling.corpus import Example, examples


def _v(value: int | float) -> dict:
    return {"value": value, "type": "value"}


CORPUS: tuple[Example, ...] = (
    examples(_v(0), ["0", "naught", "nought", "zero", "nil"]),
    examples(_v(1), ["1", "one", "single"]),
    examples(_v(2), ["2", "two", "a pair", "a couple", "a couple of"]),
    examples(_v(3), ["3", "three", "a few", "few"]),
    examples(_v(10), ["10", "ten"]),
    examples(_v(12), ["12", "twelve", "a dozen", "a dozen of"]),
    examples(_v(14), ["14", "fourteen"]),
    examples(_v(16), ["16", "sixteen"]),
    examples(_v(17), ["17", "seventeen"]),
    examples(_v(18), ["18", "eighteen"]),
    examples(_v(33), ["33", "thirty three", "0033"]),
    examples(_v(24), ["24", "2 dozens", "two dozen", "Two dozen"]),
    examples(_v(1.1), ["1.1", "1.10", "01.10", "1 point 1"]),
    examples(_v(0.77), [".77", "0.77", "point 77"]),
    examples(
        _v(100000),
        [
            "100,000",
            "100,000.0",
            "100000",
            "100K",
            "100k",
            "one hundred thousand",
        ],
    ),
    examples(_v(0.2), ["1/5", "2/10", "3/15", "20/100"]),
    examples(
        _v(3e6),
        [
            "3M",
            "3000K",
            "3000000",
            "3,000,000",
            "3 million",
            "30 lakh",
            "30 lkh",
            "30 l",
        ],
    ),
    examples(
        _v(1.2e6),
        [
            "1,200,000",
            "1200000",
            "1.2M",
            "1200k",
            ".0012G",
            "12 lakhs",
            "12 lkhs",
        ],
    ),
    examples(_v(5000), ["5 thousand", "five thousand"]),
    examples(_v(-504), ["-504", "negative five hundred and four"]),
    examples(
        _v(-1.2e6),
        [
            "- 1,200,000",
            "-1200000",
            "minus 1,200,000",
            "negative 1200000",
            "-1.2M",
            "-1200K",
            "-.0012G",
        ],
    ),
    examples(
        _v(-3200000),
        [
            "-3,200,000",
            "-3200000",
            "minus three million two hundred thousand",
        ],
    ),
    examples(_v(122), ["one twenty two", "ONE TwentY tWO"]),
    examples(_v(2e5), ["two Hundred thousand"]),
    examples(_v(21011), ["twenty-one thousand Eleven"]),
    examples(
        _v(721012),
        [
            "seven hundred twenty-one thousand twelve",
            "seven hundred twenty-one thousand and twelve",
        ],
    ),
    examples(
        _v(31256721),
        [
            "thirty-one million two hundred fifty-six thousand seven hundred twenty-one",
            "three crore twelve lakh fifty-six thousand seven hundred twenty-one",
            "three cr twelve lac fifty-six thousand seven hundred twenty-one",
        ],
    ),
    examples(_v(2400), ["two hundred dozens", "200 dozens"]),
    examples(_v(2200000), ["two point two million"]),
    examples(
        _v(3000000000),
        [
            "three billions",
            "three thousand millions",
            "three hundred crores",
            "three hundred Cr",
            "three hundred koti",
            "three hundred krores",
            "three hundred Kr",
        ],
    ),
    examples(_v(45), ["forty-five (45)", "45 (forty five)"]),
)
