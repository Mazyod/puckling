"""Rules for the locale-agnostic ``credit_card`` dimension.

Faithful Python port of Duckling's ``Duckling/CreditCardNumber/Rules.hs`` and
``Duckling/CreditCardNumber/Helpers.hs``: one rule per issuer, each matching a
specific BIN-informed pattern and validated by the Luhn checksum. A fallback
rule catches generic 8-19 digit sequences that do not match any issuer-specific
pattern.
"""

from __future__ import annotations

from puckling.dimensions.credit_card.types import CreditCardValue
from puckling.types import RegexMatch, Rule, Token, regex

# Min/max digit counts mirror Duckling's ``minNumberDigits``/``maxNumberDigits``.
_MIN_DIGITS = 8
_MAX_DIGITS = 19


# ---------------------------------------------------------------------------
# Issuer-specific regex fragments (BIN-informed; mirror upstream Helpers.hs).
#
# Each fragment accepts either no separators or one consistent separator
# (dash or ASCII space) at the upstream-specified group boundaries. Upstream
# Duckling only allows dashes; puckling extends to ASCII spaces so common
# copy-paste forms parse.
# TODO(puckling): edge case — narrow to dashes only if strict upstream parity
# is required.

_VISA = (
    r"(?:4[0-9]{15}"
    r"|4[0-9]{3}-[0-9]{4}-[0-9]{4}-[0-9]{4}"
    r"|4[0-9]{3} [0-9]{4} [0-9]{4} [0-9]{4})"
)
_AMEX = (
    r"(?:3[47][0-9]{13}"
    r"|3[47][0-9]{2}-[0-9]{6}-[0-9]{5}"
    r"|3[47][0-9]{2} [0-9]{6} [0-9]{5})"
)
_DISCOVER = (
    r"(?:6(?:011|[45][0-9]{2})[0-9]{12}"
    r"|6(?:011|[45][0-9]{2})-[0-9]{4}-[0-9]{4}-[0-9]{4}"
    r"|6(?:011|[45][0-9]{2}) [0-9]{4} [0-9]{4} [0-9]{4})"
)
_MASTERCARD = (
    r"(?:5[1-5][0-9]{14}"
    r"|5[1-5][0-9]{2}-[0-9]{4}-[0-9]{4}-[0-9]{4}"
    r"|5[1-5][0-9]{2} [0-9]{4} [0-9]{4} [0-9]{4})"
)
_DINER_CLUB = (
    r"(?:3(?:0[0-5]|[68][0-9])[0-9]{11}"
    r"|3(?:0[0-5]|[68][0-9])[0-9]-[0-9]{6}-[0-9]{4}"
    r"|3(?:0[0-5]|[68][0-9])[0-9] [0-9]{6} [0-9]{4})"
)

# The "other" pattern excludes any of the issuer-specific patterns so it acts
# as a true fallback. This mirrors the negative-lookahead chain in Helpers.hs.
_OTHER = (
    rf"(?:(?!{_VISA})(?!{_AMEX})(?!{_DISCOVER})(?!{_MASTERCARD})(?!{_DINER_CLUB})"
    rf"[0-9]{{{_MIN_DIGITS},{_MAX_DIGITS}}})"
)


# ---------------------------------------------------------------------------
# Luhn validation (mirrors ``isValidCreditCardNumber`` in Helpers.hs).


def _luhn(digits: str) -> bool:
    """Return ``True`` iff ``digits`` is a valid Luhn checksum."""
    total = 0
    # Walk from rightmost digit; double every second digit (the second-to-last,
    # fourth-to-last, ...) and sum its decimal digits.
    for i, ch in enumerate(reversed(digits)):
        d = ord(ch) - ord("0")
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _is_valid(digits: str) -> bool:
    return _MIN_DIGITS <= len(digits) <= _MAX_DIGITS and _luhn(digits)


# ---------------------------------------------------------------------------
# Production factory.


def _make_prod(issuer: str):
    """Build a production that emits a credit-card token for ``issuer``."""

    def prod(tokens: tuple[Token, ...]) -> Token | None:
        match = tokens[0]
        if not isinstance(match.value, RegexMatch):
            return None
        # Canonical card number is digits-only — mirrors ``T.filter C.isDigit``.
        digits = "".join(ch for ch in match.value.text if ch.isdigit())
        if not _is_valid(digits):
            return None
        return Token(
            dim="credit_card",
            value=CreditCardValue(value=digits, issuer=issuer),
        )

    return prod


def _make_rule(name: str, pattern: str, issuer: str) -> Rule:
    # Wrap each pattern in token-boundary lookarounds so we never match inside
    # a longer identifier/number or consume the valid prefix of a malformed
    # dash-separated run. Upstream Duckling relies on a learned ranker
    # (Duckling.Ranking) to discard such partial matches; puckling has no
    # ranker yet, so we enforce whole-number semantics via the regex.
    # TODO(puckling): edge case — drop boundaries once ranking is implemented.
    anchored = rf"(?<![\p{{L}}\p{{N}}_-]){pattern}(?![\p{{L}}\p{{N}}_-])"
    return Rule(name=name, pattern=(regex(anchored),), prod=_make_prod(issuer))


RULES: tuple[Rule, ...] = (
    _make_rule("visa credit card number", _VISA, "visa"),
    _make_rule("amex card number", _AMEX, "amex"),
    _make_rule("discover card number", _DISCOVER, "discover"),
    _make_rule("mastercard card number", _MASTERCARD, "mastercard"),
    _make_rule("diner club card number", _DINER_CLUB, "diner club"),
    _make_rule("credit card number", _OTHER, "other"),
)


__all__ = ["RULES"]
