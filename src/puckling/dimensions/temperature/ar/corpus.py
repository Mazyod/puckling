"""Temperature corpus — Arabic.

Ported from Duckling/Temperature/AR/Corpus.hs. Phrases that depend on
spelled-out Arabic numerals (e.g. "سبع وثلاثون") are deferred to AR Numeral.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    examples(
        {"value": 37, "unit": "celsius", "type": "value"},
        [
            "37° سلزيوس",
            "37 ° سلزيوس",
            "37 درجة سلزيوس",
            "٣٧° سلزيوس",
            # TODO(puckling): edge case — "سبع وثلاثون سلزيوس" needs AR spelled-out numerals.
        ],
    ),
    examples(
        {"value": 30, "unit": "celsius", "type": "value"},
        [
            "30 درجة مئوية",
            "٣٠ درجة مئوية",
            "30 سلزيوس",
            "٣٠°س",
            "30 °س",
        ],
    ),
    examples(
        {"value": 30.5, "unit": "celsius", "type": "value"},
        [
            "٣٠.٥ درجة مئوية",
        ],
    ),
    examples(
        {"value": 70, "unit": "fahrenheit", "type": "value"},
        [
            "70° فهرنهايت",
            "70 درجة فهرنهايت",
            "٧٠ فهرنهايت",
            # TODO(puckling): edge case — "سبعون فهرنهايت" needs AR spelled-out numerals.
        ],
    ),
    examples(
        {"value": 2.5, "unit": "degree", "type": "value"},
        [
            "٢٫٥ درجة",
        ],
    ),
    examples(
        {"value": 45, "unit": "degree", "type": "value"},
        [
            "45°",
            "45 درجة",
            "45 درجه مئوية",
        ],
    ),
    examples(
        {"value": -2, "unit": "degree", "type": "value"},
        [
            "-2°",
            "- 2 درجة",
            "-٢ درجة",
            "درجتين تحت الصفر",
            "2 تحت الصفر",
        ],
    ),
    examples(
        {"value": 2, "unit": "degree", "type": "value"},
        [
            "درجتان",
        ],
    ),
)
