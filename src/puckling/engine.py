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

The engine enforces three caps to prevent runaway parses on pathological
inputs (token-explosion under composition):

- `max_iterations`: outer saturation iterations.
- `time_budget_ms`: wall-clock budget across the whole call.
- `max_tokens`: hard cap on total token forest size.

When any cap is hit, the engine returns whatever tokens it has accumulated so
far. Callers ranking the results still get a valid (possibly partial) parse.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from dataclasses import replace
from functools import lru_cache
from typing import cast

from puckling.types import (
    Pattern,
    PatternItem,
    Range,
    RegexItem,
    RegexMatch,
    Rule,
    Token,
)

_EXACT_DIM_ATTR = "__puckling_exact_dim__"


class _TokenIndex:
    __slots__ = ("by_start", "starts")

    def __init__(
        self,
        by_start: dict[int, list[Token]],
        starts: tuple[int, ...],
    ) -> None:
        self.by_start = by_start
        self.starts = starts


# A specialized matcher function: given the source text, a position, and the
# current token index, yield tokens that match this pattern slot.
# Built once per pattern item via `_make_matcher` and cached, so the hot
# loop pays no `isinstance` per probe.
_RegexMatchMemo = dict[tuple[int, int], Token | object]
_Matcher = Callable[[str, int, _TokenIndex, _RegexMatchMemo], Iterator[Token]]
_REGEX_CACHE_MISS = object()
_REGEX_NO_MATCH = object()

# Maximum saturation iterations — guards against pathological rule sets.
DEFAULT_MAX_ITERATIONS = 50
# Wall-clock cap (ms) for a single `parse_and_resolve` call. Set to `None` to
# disable. Default is generous enough for real production inputs but tight
# enough that a runaway parse aborts in seconds, not minutes.
DEFAULT_TIME_BUDGET_MS: int | None = 2000
# Hard cap on the total token forest size. Cheap to enforce and deterministic.
DEFAULT_MAX_TOKENS = 10_000


class _ParseBudgetExceeded(Exception):
    """Raised internally when any of the engine's caps is hit. Caught by `parse_and_resolve`."""


def _skip_whitespace(text: str, pos: int) -> int:
    """Advance `pos` past ASCII or Unicode whitespace."""
    n = len(text)
    while pos < n and text[pos].isspace():
        pos += 1
    return pos


def _make_matcher(item: PatternItem) -> _Matcher:
    """Specialize a matcher function for one pattern slot.

    Closes over the regex / predicate so the hot loop calls it directly
    without re-checking the slot type per probe. See PERF_FINDINGS.md for
    measurements.
    """
    if isinstance(item, RegexItem):
        compiled = item.compiled
        assert compiled is not None
        compiled_id = id(compiled)

        def _match_regex(
            text: str,
            pos: int,
            token_index: _TokenIndex,
            regex_match_memo: _RegexMatchMemo,
        ) -> Iterator[Token]:
            key = (compiled_id, pos)
            cached = regex_match_memo.get(key, _REGEX_CACHE_MISS)
            if cached is _REGEX_CACHE_MISS:
                m = compiled.match(text, pos=pos)
                if m is not None and m.end() > m.start():
                    cached = Token(
                        dim="regex_match",
                        value=RegexMatch(text=m.group(0), groups=tuple(m.groups())),
                        range=Range(m.start(), m.end()),
                    )
                else:
                    cached = _REGEX_NO_MATCH
                regex_match_memo[key] = cached
            if cached is not _REGEX_NO_MATCH:
                yield cast(Token, cached)

        return _match_regex

    # PredicateItem
    fn = item.fn
    exact_dim = getattr(fn, _EXACT_DIM_ATTR, None)
    if exact_dim is not None:

        def _match_exact_dim(
            text: str,
            pos: int,
            token_index: _TokenIndex,
            regex_match_memo: _RegexMatchMemo,
        ) -> Iterator[Token]:
            bucket = token_index.by_start.get(pos)
            if bucket is None:
                return
            for tok in bucket:
                if tok.dim == exact_dim:
                    yield tok

        return _match_exact_dim

    def _match_predicate(
        text: str,
        pos: int,
        token_index: _TokenIndex,
        regex_match_memo: _RegexMatchMemo,
    ) -> Iterator[Token]:
        bucket = token_index.by_start.get(pos)
        if bucket is None:
            return
        for tok in bucket:
            if fn(tok):
                yield tok

    return _match_predicate


@lru_cache(maxsize=4096)
def _matchers_for_pattern(pattern: Pattern) -> tuple[_Matcher, ...]:
    """One matcher per pattern slot, cached by pattern identity.

    Bounded purely as defense in depth — puckling's static rule set has
    only a few hundred distinct patterns.
    """
    return tuple(_make_matcher(item) for item in pattern)


def _match_pattern_from(
    matchers: tuple[_Matcher, ...],
    text: str,
    pos: int,
    token_index: _TokenIndex,
    regex_match_memo: _RegexMatchMemo,
) -> Iterator[tuple[Token, ...]]:
    """Yield every full match of `matchers` starting at `pos`."""
    if not matchers:
        yield ()
        return
    head, tail = matchers[0], matchers[1:]
    for tok in head(text, pos, token_index, regex_match_memo):
        next_pos = _skip_whitespace(text, tok.range.end)
        for rest in _match_pattern_from(
            tail, text, next_pos, token_index, regex_match_memo
        ):
            yield (tok, *rest)


def _apply_rule(
    rule: Rule,
    text: str,
    token_index: _TokenIndex,
    regex_match_memo: _RegexMatchMemo,
) -> list[Token]:
    """Run `rule` against `text + tokens`, returning newly produced tokens.

    Specialises three cases for performance:

    1. Single-item regex pattern → drive with a single overlapped `finditer`
       call instead of `n+1` anchored `regex.match` calls. Roughly the cost
       of one regex sweep instead of `n+1`.
    2. Single-item predicate pattern → iterate only token start positions
       (from `tokens_by_start`) instead of every text position.
    3. Multi-item pattern → fall back to the general per-position match.

    The single-item fast paths intentionally inline the matching logic
    that `_make_matcher` would otherwise wrap in a closure — keep them in
    sync if you change one. Factoring them through the matcher framework
    re-imposes the closure call overhead the specialization is meant to
    avoid.
    """
    pattern = rule.pattern
    matchers = _matchers_for_pattern(pattern)
    out: list[Token] = []
    name = rule.name
    prod = rule.prod

    if len(matchers) == 1:
        head_item = pattern[0]
        if isinstance(head_item, RegexItem):
            compiled = head_item.compiled
            assert compiled is not None
            for m in compiled.finditer(text, overlapped=True):
                if m.end() == m.start():
                    continue
                tok = Token(
                    dim="regex_match",
                    value=RegexMatch(text=m.group(0), groups=tuple(m.groups())),
                    range=Range(m.start(), m.end()),
                )
                produced = prod((tok,))
                if produced is None:
                    continue
                out.append(replace(produced, range=tok.range, produced_by=name))
            return out

        # PredicateItem — iterate only positions where tokens exist.
        # Visit positions in text order to preserve the ordering the original
        # `for start in range(n+1)` loop produced. `tokens_by_start.items()`
        # would be insertion-order (i.e. token-production order across earlier
        # rules), which would change `analyze()` output order and which tokens
        # survive a `max_tokens` truncation.
        fn = head_item.fn
        exact_dim = getattr(fn, _EXACT_DIM_ATTR, None)
        if exact_dim is not None:
            for start in token_index.starts:
                for tok in token_index.by_start[start]:
                    if tok.dim == exact_dim:
                        produced = prod((tok,))
                        if produced is None:
                            continue
                        out.append(
                            replace(produced, range=tok.range, produced_by=name)
                        )
            return out

        for start in token_index.starts:
            for tok in token_index.by_start[start]:
                if fn(tok):
                    produced = prod((tok,))
                    if produced is None:
                        continue
                    out.append(
                        replace(produced, range=tok.range, produced_by=name)
                    )
        return out

    n = len(text)
    for start in range(n + 1):
        for matched in _match_pattern_from(
            matchers, text, start, token_index, regex_match_memo
        ):
            if not matched:
                continue
            produced = prod(matched)
            if produced is None:
                continue
            full_range = Range(matched[0].range.start, matched[-1].range.end)
            out.append(replace(produced, range=full_range, produced_by=name))
    return out


def _index_tokens(tokens: list[Token]) -> _TokenIndex:
    by_start: dict[int, list[Token]] = {}
    for t in tokens:
        start = t.range.start
        bucket = by_start.get(start)
        if bucket is None:
            by_start[start] = [t]
        else:
            bucket.append(t)
    return _TokenIndex(by_start, tuple(sorted(by_start)))


def _token_key(t: Token) -> tuple:
    return (t.dim, t.range.start, t.range.end, t.value)


def _depends_on_tokens(rule: Rule) -> bool:
    """Whether `rule` needs the evolving token forest to match."""
    return any(not isinstance(item, RegexItem) for item in rule.pattern)


@lru_cache(maxsize=512)
def _token_dependent_rules(rules: tuple[Rule, ...]) -> tuple[Rule, ...]:
    return tuple(rule for rule in rules if _depends_on_tokens(rule))


def parse_and_resolve(
    rules: tuple[Rule, ...],
    text: str,
    *,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    time_budget_ms: int | None = DEFAULT_TIME_BUDGET_MS,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> list[Token]:
    """Saturating fixed-point parser.

    Returns every token produced by any rule, in production order. Callers are
    responsible for filtering to non-overlapping winners (see `puckling.api`).

    On budget exhaustion (`time_budget_ms` or `max_tokens`), returns whatever
    tokens were accumulated up to that point.
    """
    deadline: float | None = None
    if time_budget_ms is not None:
        deadline = time.monotonic() + time_budget_ms / 1000.0

    tokens: list[Token] = []
    seen: set[tuple] = set()
    token_dependent_rules = _token_dependent_rules(rules)
    regex_match_memo: _RegexMatchMemo = {}

    try:
        for iteration in range(max_iterations):
            if deadline is not None and time.monotonic() > deadline:
                break
            if len(tokens) >= max_tokens:
                break
            # Rebuild the token lookup index once per saturation pass.
            # Rules within the same pass see the same snapshot, so this is
            # safe to cache across the inner rule loop.
            token_index = _index_tokens(tokens)
            new_tokens: list[Token] = []
            active_rules = rules if iteration == 0 else token_dependent_rules
            for rule in active_rules:
                # Coarse deadline check at rule boundaries — cheap (~200/iter).
                if deadline is not None and time.monotonic() > deadline:
                    raise _ParseBudgetExceeded()
                for tok in _apply_rule(rule, text, token_index, regex_match_memo):
                    key = _token_key(tok)
                    if key in seen:
                        continue
                    seen.add(key)
                    new_tokens.append(tok)
                    if len(tokens) + len(new_tokens) >= max_tokens:
                        raise _ParseBudgetExceeded()
            if not new_tokens:
                break
            tokens.extend(new_tokens)
            if not token_dependent_rules:
                break
    except _ParseBudgetExceeded:
        pass

    return tokens
