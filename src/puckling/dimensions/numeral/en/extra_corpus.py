"""Supplemental English Numeral corpus — phrase variants beyond the upstream base set.

Adds coverage for variants that the rules already support but the upstream
`Duckling/Numeral/EN/Corpus.hs` does not enumerate (informal synonyms, more
units/teens/tens, dashed/spaced composites, "and"-joined hundreds, K/M/G
suffix variants, fractions, parens form, dozen multipliers, Indian-system
multipliers, etc.).
"""

from __future__ import annotations

from puckling.corpus import Example, examples


def _v(value: int | float) -> dict:
    return {"value": value, "type": "value"}


CORPUS: tuple[Example, ...] = (
    # Zero variants beyond the upstream base set.
    examples(_v(0), ["none", "zilch", "00", "000"]),
    # Informal "single" already covered upstream; add "pair"/"couple" variants.
    examples(
        _v(2),
        [
            "pair",
            "pairs",
            "pair of",
            "pairs of",
            "a pair of",
            "couple",
            "couples",
            "couple of",
            "couples of",
        ],
    ),
    # Units 4..9 are not enumerated in upstream's allExamples.
    examples(_v(4), ["four"]),
    examples(_v(5), ["5", "five"]),
    examples(_v(6), ["six"]),
    examples(_v(7), ["seven", "07"]),
    examples(_v(8), ["eight"]),
    examples(_v(9), ["nine"]),
    # Teens not enumerated upstream.
    examples(_v(11), ["11", "eleven"]),
    examples(_v(13), ["13", "thirteen"]),
    examples(_v(15), ["15", "fifteen"]),
    examples(_v(19), ["19", "nineteen"]),
    # Tens (20..90) — none of these are exercised individually upstream.
    examples(_v(20), ["20", "twenty"]),
    examples(_v(30), ["30", "thirty"]),
    examples(_v(40), ["40", "forty", "fourty"]),
    examples(_v(50), ["50", "fifty"]),
    examples(_v(60), ["60", "sixty"]),
    examples(_v(70), ["70", "seventy"]),
    examples(_v(80), ["80", "eighty"]),
    examples(_v(90), ["90", "ninety"]),
    examples(_v(42), ["42", "forty two", "forty-two", "042"]),
    # Composite tens (dashed and spaced) for additional units.
    examples(_v(51), ["fifty one", "fifty-one"]),
    examples(_v(62), ["sixty two", "sixty-two"]),
    examples(_v(78), ["seventy eight", "seventy-eight"]),
    examples(_v(89), ["eighty nine", "eighty-nine"]),
    examples(_v(99), ["ninety nine", "ninety-nine"]),
    # "one eleven" pattern (skip-hundreds 1) — additional coverage.
    examples(_v(211), ["two eleven"]),
    examples(_v(312), ["three twelve"]),
    examples(_v(419), ["four nineteen"]),
    examples(_v(520), ["five twenty"]),
    examples(_v(990), ["nine ninety"]),
    # "one twenty two" pattern (skip-hundreds 2) — additional coverage.
    examples(_v(234), ["two thirty four"]),
    examples(_v(345), ["three forty five"]),
    examples(_v(999), ["nine ninety nine"]),
    # Hundreds composition.
    examples(_v(100), ["hundred", "one hundred", "a hundred"]),
    examples(_v(200), ["two hundred"]),
    examples(_v(900), ["nine hundred"]),
    examples(_v(150), ["one hundred fifty", "one hundred and fifty"]),
    examples(_v(250), ["two hundred and fifty"]),
    examples(_v(101), ["one hundred and one"]),
    examples(_v(303), ["three hundred and three"]),
    examples(_v(504), ["five hundred and four", "five hundred four"]),
    examples(_v(1300), ["thirteen hundred"]),
    examples(_v(1200), ["twelve hundred"]),
    examples(_v(1500), ["fifteen hundred", "one thousand five hundred"]),
    # Thousands, millions, billions.
    examples(_v(1000), ["thousand", "one thousand", "a thousand"]),
    examples(_v(2000), ["2 thousand", "two thousand"]),
    examples(_v(10000), ["ten thousand", "10 thousand"]),
    examples(_v(50000), ["fifty thousand"]),
    examples(_v(2500), ["two thousand five hundred"]),
    examples(_v(2050), ["two thousand and fifty"]),
    examples(_v(2100), ["two thousand one hundred"]),
    examples(_v(1e6), ["one million", "a million", "1 million"]),
    examples(_v(2e6), ["two million"]),
    examples(_v(5e8), ["500 million"]),
    examples(_v(1.5e6), ["1.5 million"]),
    examples(_v(1e9), ["one billion", "1 billion"]),
    examples(_v(2e9), ["two billion"]),
    # Decimals and "point".
    examples(_v(0.5), [".5", "0.5", "point 5", "point five"]),
    examples(_v(2.5), ["2.5", "2 point 5"]),
    examples(_v(3.14), ["3.14"]),
    examples(_v(100.5), ["100.5"]),
    examples(_v(1.5), ["one dot five"]),
    examples(
        _v(1.25),
        [
            "one point twenty five",
            "one point twenty-five",
            "one dot twenty five",
            "one dot twenty-five",
        ],
    ),
    # K/M/G suffixes — additional values.
    examples(_v(5000), ["5K", "5k"]),
    examples(_v(500000), ["500K", "500k"]),
    examples(_v(2e6), ["2M", "2m"]),
    examples(_v(2.5e6), ["2.5M"]),
    examples(_v(1e9), ["1G", "1g"]),
    # Negative numbers.
    examples(_v(-1), ["-1", "minus 1", "negative 1", "- 1"]),
    examples(_v(-5), ["-5", "minus five"]),
    examples(_v(-10), ["-10", "negative ten"]),
    examples(_v(-100), ["-100", "minus 100", "minus one hundred"]),
    examples(_v(-1000), ["-1000", "negative one thousand"]),
    examples(_v(-0.5), ["-.5", "minus .5", "minus point five", "negative point five"]),
    examples(_v(-1e6), ["-1M", "minus one million"]),
    examples(_v(-2e6), ["negative two million"]),
    examples(_v(-1e9), ["-1G"]),
    # Fractions.
    examples(_v(0.5), ["1/2", "3/6", "5/10"]),
    examples(_v(0.25), ["1/4"]),
    examples(_v(0.75), ["3/4"]),
    examples(_v(0.875), ["7/8"]),
    examples(_v(0.1), ["10/100"]),
    # Comma-grouped numbers.
    examples(_v(1000), ["1,000"]),
    examples(_v(10000), ["10,000"]),
    examples(_v(1e6), ["1,000,000"]),
    examples(_v(1234567.89), ["1,234,567.89"]),
    # Parens form `<integer> (<integer>)`.
    examples(_v(20), ["twenty (20)", "20 (twenty)"]),
    examples(_v(5), ["(5)"]),
    # Dozen multiplier (beyond the upstream `2 dozens`/`two dozen`).
    examples(_v(12), ["dozen", "dozens", "a dozen"]),
    examples(_v(36), ["three dozen", "a few dozen"]),
    examples(_v(48), ["four dozens"]),
    examples(_v(24), ["a couple of dozen"]),
    # Indian-system multipliers (additional values).
    examples(_v(1e7), ["1 crore", "one crore", "one hundred lakh"]),
    examples(_v(500000), ["5 lakh"]),
    examples(_v(100000), ["one lac"]),
    examples(_v(5e8), ["fifty crore"]),
    # TODO(puckling): edge case — `trillion` defined in the lookup map but
    # the powers-of-ten regex doesn't include it, so "one trillion" misparses.
    # TODO(puckling): edge case — `half` is not modeled by the numeral rules.
    # TODO(puckling): edge case — `point seven five` only consumes one digit.
)
