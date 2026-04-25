"""Email dimension corpus — ported from Duckling's ``Duckling/Email/Corpus.hs``."""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    examples({"value": "alice@exAmple.io", "type": "value"}, ["alice@exAmple.io"]),
    examples({"value": "yo+yo@blah.org", "type": "value"}, ["yo+yo@blah.org"]),
    examples({"value": "1234+abc@x.net", "type": "value"}, ["1234+abc@x.net"]),
    examples(
        {"value": "jean-jacques@stuff.co.uk", "type": "value"},
        ["jean-jacques@stuff.co.uk"],
    ),
)


# Phrases that must NOT produce an email entity (Duckling's negativeCorpus).
NEGATIVE_CORPUS: tuple[str, ...] = (
    "hey@6",
    "hey@you",
)
