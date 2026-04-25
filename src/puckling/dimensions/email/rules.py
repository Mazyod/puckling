"""Email dimension rules — locale-agnostic.

Ported from Duckling's ``Duckling/Email/Rules.hs``. The single rule matches a
local part, ``@``, and a domain with at least one dot-separated segment.
"""

from __future__ import annotations

from puckling.dimensions.email.types import EmailValue
from puckling.types import Rule, Token, regex

# Mirrors Duckling's regex: ([\w\._+-]+@[\w_-]+(\.[\w_-]+)+)
_EMAIL_PATTERN = r"([\w\._+-]+@[\w_-]+(\.[\w_-]+)+)"


def _prod_email(tokens: tuple[Token, ...]) -> Token | None:
    return Token(dim="email", value=EmailValue(value=tokens[0].value.text))


_email_rule = Rule(
    name="email",
    pattern=(regex(_EMAIL_PATTERN),),
    prod=_prod_email,
)


RULES: tuple[Rule, ...] = (_email_rule,)
