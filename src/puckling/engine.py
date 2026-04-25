"""Saturating fixed-point parser. The heart of puckling.

The algorithm mirrors Duckling's engine:

1. For each rule, attempt to match its `pattern` starting at every position in
   the source text. The first item is anchored (regex matches at exactly that
   position; predicate matches a token whose range starts there). Subsequent
   items are anchored just after the previous match, with optional whitespace
   between.
2. When a pattern is fully matched, the rule's `prod` is invoked with the
   matched tokens. If it returns a token, that token gets the full span and is
   added to the parse forest (deduped).
3. Repeat until no new tokens appear (fixed-point saturation).

Productions are pure; rules are pure data. The engine carries no mutable state
between calls.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace

from puckling.types import (
    Pattern,
    PatternItem,
    Range,
    RegexItem,
    RegexMatch,
    Rule,
    Token,
)

# Maximum saturation iterations — guards against pathological rule sets.
DEFAULT_MAX_ITERATIONS = 50


def _skip_whitespace(text: str, pos: int) -> int:
    """Advance `pos` past ASCII or Unicode whitespace."""
    n = len(text)
    while pos < n and text[pos].isspace():
        pos += 1
    return pos


def _match_item_at(
    item: PatternItem,
    text: str,
    pos: int,
    tokens: list[Token],
) -> Iterator[Token]:
    """Yield tokens matching `item` anchored at exactly `pos`."""
    if isinstance(item, RegexItem):
        assert item.compiled is not None
        m = item.compiled.match(text, pos=pos)
        if m is not None and m.end() > m.start():
            yield Token(
                dim="regex_match",
                value=RegexMatch(text=m.group(0), groups=tuple(m.groups())),
                range=Range(m.start(), m.end()),
            )
        return
    # PredicateItem
    for tok in tokens:
        if tok.range.start == pos and item.fn(tok):
            yield tok


def _match_pattern_from(
    pattern: Pattern,
    text: str,
    pos: int,
    tokens: list[Token],
) -> Iterator[tuple[Token, ...]]:
    """Yield every full match of `pattern` starting at `pos`."""
    if not pattern:
        yield ()
        return
    head, tail = pattern[0], pattern[1:]
    for tok in _match_item_at(head, text, pos, tokens):
        next_pos = _skip_whitespace(text, tok.range.end)
        for rest in _match_pattern_from(tail, text, next_pos, tokens):
            yield (tok, *rest)


def _apply_rule(rule: Rule, text: str, tokens: list[Token]) -> list[Token]:
    """Run `rule` against `text + tokens`, returning newly produced tokens."""
    out: list[Token] = []
    n = len(text)
    for start in range(n + 1):
        for matched in _match_pattern_from(rule.pattern, text, start, tokens):
            if not matched:
                continue
            produced = rule.prod(matched)
            if produced is None:
                continue
            full_range = Range(matched[0].range.start, matched[-1].range.end)
            out.append(replace(produced, range=full_range, produced_by=rule.name))
    return out


def _token_key(t: Token) -> tuple:
    return (t.dim, t.range.start, t.range.end, t.value)


def parse_and_resolve(
    rules: tuple[Rule, ...],
    text: str,
    *,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
) -> list[Token]:
    """Saturating fixed-point parser.

    Returns every token produced by any rule, in production order. Callers are
    responsible for filtering to non-overlapping winners (see `puckling.api`).
    """
    tokens: list[Token] = []
    seen: set[tuple] = set()

    for _ in range(max_iterations):
        new_tokens: list[Token] = []
        for rule in rules:
            for tok in _apply_rule(rule, text, tokens):
                key = _token_key(tok)
                if key in seen:
                    continue
                seen.add(key)
                new_tokens.append(tok)
        if not new_tokens:
            break
        tokens.extend(new_tokens)

    return tokens
