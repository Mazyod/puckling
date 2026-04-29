"""Phone number rules for English.

Ported from Duckling's locale-agnostic ``Duckling/PhoneNumber/Rules.hs``. Phone
numbers vary widely; the regex below matches typical international and
US-style formats (optional country code, optional area code in parens, common
separators).
"""

from __future__ import annotations

from puckling.dimensions.phone_number.types import phone
from puckling.types import Rule, Token, regex

# TODO(puckling): edge case — upstream supports an optional ``ext NNN`` suffix
# and a 6-character minimum digit count enforced via lookahead. We omit those
# here because the simplified pattern below is sufficient for the EN corpus.
_PHONE_BODY = (
    r"(?:\+?\d{1,3}[ .-]?)?"
    r"(?:\(?\d{2,4}\)?[ .-]?)?"
    r"\d{3,4}[ .-]?\d{3,4}"
    r"(?:[ .-]?\d{2,4})?"
)
_PHONE_PATTERN = rf"(?<![\w@/.:=&%+#-]){_PHONE_BODY}(?![\w@/])(?!(?:[.-]\d))"


def _to_phone(toks: tuple[Token, ...]) -> Token | None:
    return Token(dim="phone_number", value=phone(toks[0].value.text))


RULES: tuple[Rule, ...] = (
    Rule(
        name="phone number",
        pattern=(regex(_PHONE_PATTERN),),
        prod=_to_phone,
    ),
)
