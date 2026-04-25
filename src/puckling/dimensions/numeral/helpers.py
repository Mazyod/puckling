"""Helpers shared by Numeral rule files for both EN and AR.

Workers building Numeral rules import from here; they do NOT need to redefine
these utilities.
"""

from __future__ import annotations

from puckling.dimensions.numeral.types import NumeralValue
from puckling.types import Token


def _value(t: Token) -> int | float | None:
    if t.dim != "numeral":
        return None
    v = t.value.value if isinstance(t.value, NumeralValue) else None
    return v


def multiply(left: Token, right: Token) -> NumeralValue | None:
    """Compose by multiplication: e.g. 5 * 100 → 500."""
    a, b = _value(left), _value(right)
    if a is None or b is None:
        return None
    return NumeralValue(value=a * b)


def add(left: Token, right: Token) -> NumeralValue | None:
    """Compose by addition: e.g. 100 + 5 → 105."""
    a, b = _value(left), _value(right)
    if a is None or b is None:
        return None
    return NumeralValue(value=a + b)


# Map digits 0-9 in Arabic-Indic script (٠-٩) to ASCII.
_ARABIC_INDIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def parse_arabic_int(text: str) -> int:
    """Parse a string of Arabic-Indic or ASCII digits into an int."""
    return int(text.translate(_ARABIC_INDIC_DIGITS))


def parse_arabic_decimal(text: str) -> float:
    """Parse a decimal expressed in Arabic-Indic or ASCII digits, with `.` or `٫` as separator."""
    normalised = text.translate(_ARABIC_INDIC_DIGITS).replace("٫", ".")
    return float(normalised)
