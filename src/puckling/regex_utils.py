"""Unicode-aware regex helpers, wrapping the third-party `regex` module.

Duckling uses PCRE; Python's stdlib `re` lacks adequate Unicode property support
for Arabic, so we route everything through the `regex` package.
"""

from __future__ import annotations

import regex as _regex

# Default flags for puckling rules.
DEFAULT_FLAGS = _regex.IGNORECASE | _regex.UNICODE


def compile_pattern(pattern: str, flags: int = 0) -> _regex.Pattern[str]:
    """Compile a pattern with puckling's default flags."""
    return _regex.compile(pattern, flags=flags | DEFAULT_FLAGS)


def match_at(pat: _regex.Pattern[str], text: str, pos: int) -> _regex.Match[str] | None:
    """Match `pat` against `text` anchored at `pos` (no advance)."""
    return pat.match(text, pos=pos)
