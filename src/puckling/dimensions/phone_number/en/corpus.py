"""English phone number corpus.

Ported from Duckling's ``Duckling/PhoneNumber/Corpus.hs`` and tailored for
EN-style numbers. Because the EN production preserves the matched text as-is
(no upstream-style normalization), each phrase resolves to its own value.
"""

from __future__ import annotations

from puckling.corpus import Example, examples


def _self_example(phrase: str) -> Example:
    """Phrase whose resolved value equals the raw matched text."""
    return examples({"value": phrase, "type": "value"}, [phrase])

CORPUS: tuple[Example, ...] = tuple(
    _self_example(phrase)
    for phrase in (
        "(415) 555-1212",
        "415-555-1212",
        "415.555.1212",
        "+1 415 555 1212",
        "+1-202-555-0121",
        "650-701-8887",
        "06 2070 2220",
        "18998078030",
    )
)
