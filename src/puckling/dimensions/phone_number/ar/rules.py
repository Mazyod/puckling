"""Arabic phone number rules.

Locale-aware port of Duckling's `Duckling/PhoneNumber/Rules.hs`. The pattern
mirrors the upstream regex but additionally accepts Arabic-Indic digits
(U+0660..U+0669) so phrases written in Arabic numerals also resolve. Common
Middle East dialing formats (e.g. +966, +971, +965, +20) flow through the
same generic shape used by Duckling.
"""

from __future__ import annotations

from puckling.dimensions.phone_number.types import phone
from puckling.types import Rule, Token, regex

# A digit class that matches both ASCII (0-9) and Arabic-Indic (٠-٩) digits.
_DIGIT = r"[\d٠-٩]"

# Mirrors Duckling's PhoneNumber pattern: optional country code, optional area
# code in parens, then two groups of 3-4 digits separated by spaces, dots, or
# hyphens. Extended with Arabic-Indic digits via `_DIGIT`.
# TODO(puckling): edge case — extension suffixes ("ext. 123") are not parsed.
_PHONE_PATTERN = (
    rf"(?:\+?{_DIGIT}{{1,3}}[\s.-]?)?"
    rf"(?:\(?{_DIGIT}{{2,4}}\)?[\s.-]?)?"
    rf"{_DIGIT}{{3,4}}[\s.-]?{_DIGIT}{{3,4}}"
)


def _produce(toks: tuple[Token, ...]) -> Token | None:
    return Token(dim="phone_number", value=phone(toks[0].value.text))


RULES: tuple[Rule, ...] = (
    Rule(
        name="phone number (AR)",
        pattern=(regex(_PHONE_PATTERN),),
        prod=_produce,
    ),
)
