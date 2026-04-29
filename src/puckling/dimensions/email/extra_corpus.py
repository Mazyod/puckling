"""Supplemental email corpus — phrase variants and edge cases.

This module sits alongside the upstream-faithful ``corpus.py`` and exists to
exercise scenarios Duckling's tiny example list does not cover but that the
underlying regex still handles correctly: in-sentence emails, trailing
punctuation, multiple emails per phrase, miscellaneous valid local-part /
domain shapes, and clear non-email neighbours.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    # In-sentence variants of the four upstream addresses.
    examples(
        {"value": "alice@exAmple.io", "type": "value"},
        [
            "Email me at alice@exAmple.io",
            "Email me at alice@exAmple.io please",
            "My email is alice@exAmple.io.",
            "hello, alice@exAmple.io!",
        ],
    ),
    examples(
        {"value": "yo+yo@blah.org", "type": "value"},
        [
            "Send to yo+yo@blah.org please",
            "Send to yo+yo@blah.org, thanks",
            "(yo+yo@blah.org)",
        ],
    ),
    examples(
        {"value": "1234+abc@x.net", "type": "value"},
        [
            "Contact: 1234+abc@x.net",
            "1234+abc@x.net is my work email",
            "<1234+abc@x.net>",
        ],
    ),
    examples(
        {"value": "jean-jacques@stuff.co.uk", "type": "value"},
        [
            "Reach me: jean-jacques@stuff.co.uk!",
            "jean-jacques@stuff.co.uk works",
            'Quote: "jean-jacques@stuff.co.uk"',
            "jean-jacques@stuff.co.uk;next",
        ],
    ),
    # Misc valid shapes: dotted local part, deeper TLD chains, leading
    # underscore, mixed case, and ``+``-tagged addresses.
    examples(
        {"value": "a.b.c@x.y.z.io", "type": "value"},
        ["mail a.b.c@x.y.z.io now", "a.b.c@x.y.z.io"],
    ),
    examples(
        {"value": "_underscore@example.com", "type": "value"},
        ["_underscore@example.com", "use _underscore@example.com instead"],
    ),
    examples(
        {"value": "CASE@MIXED.Org", "type": "value"},
        ["CASE@MIXED.Org", "ping CASE@MIXED.Org if needed"],
    ),
    examples(
        {"value": "name+tag@example.co", "type": "value"},
        ["name+tag@example.co", "send to name+tag@example.co for routing"],
    ),
    examples(
        {"value": "first.last+tag@sub.example.co.uk", "type": "value"},
        [
            "first.last+tag@sub.example.co.uk",
            "route first.last+tag@sub.example.co.uk today",
        ],
    ),
    examples(
        {"value": "first_last@example-domain.com", "type": "value"},
        [
            "first_last@example-domain.com",
            "Use first_last@example-domain.com for alerts",
        ],
    ),
)


# Phrases containing more than one valid email; both must surface.
MULTI_EMAIL_CORPUS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Two emails: alice@exAmple.io and yo+yo@blah.org",
        ("alice@exAmple.io", "yo+yo@blah.org"),
    ),
    (
        "Cc 1234+abc@x.net, jean-jacques@stuff.co.uk please",
        ("1234+abc@x.net", "jean-jacques@stuff.co.uk"),
    ),
)


# Phrases that must NOT produce an email entity. Mirrors upstream's
# negativeCorpus plus focused neighbour cases that should also be rejected.
NEGATIVE_CORPUS: tuple[str, ...] = (
    "hey@6",
    "hey@you",
    "no-at-sign-here.com",
    "@no-local-part.com",
    "trailing-at@",
    "empty@",
    "foo@",
    "foo@bar",
    "foo@example",
    "foo@example.",
    "foo@.example.com",
    "foo@example..com",
    "foo@@example.com",
    "foo@bar .com",
    "foo@bar. com",
    "foo!@example.com",
    "foo()@example.com",
    "http://foo@bar",
    "https://example.com/@support",
    "https://example.com/user@example",
    "example.com/@support",
)
