# Phase 1 — Python micro-optimizations

Originally explored on the `perf/python-micro-opts` branch (since retired). Shipped to `main` and released as v0.2.0. Baseline: `bench/results/baseline-micro-opts.json` (post-deadline-fix `main`).

## Headline

| Cell | Baseline | After | Δ |
|---|---:|---:|---:|
| `en/multi/long` "transfer 100 KWD…" | 27.97ms | **12.55ms** | **−55.1%** |
| `en/email/medium` "my email is alice@…" | 10.90ms | 4.79ms | −56.0% |
| `en/url/medium` "visit https://…" | 12.18ms | 5.19ms | −57.4% |
| `en/sat/long` "the third Monday of October 2014" | 17.53ms | 8.32ms | −52.5% |
| `ar/multi/long` "حول ١٠٠ دينار كويتي…" | 9.09ms | 2.05ms | −77.4% |
| `ar/no-entity/short` "مرحبا" | 1.02ms | 0.14ms | −86.2% |

**Mean improvement across all 28 cells: ≈ 60-70%.** Every cell improved.

## Changes (in order of application)

### RANK 1 — Cache `rules_for(lang, dims)` on the registry  *(−4 to −71%, fixed-cost dominator on shorts)*
`@functools.cache` on `_registry.rules_for`. Module set is static at runtime. Was 9.8% of cumtime per parse via `pkgutil.iter_modules` + `posix.listdir` re-scans.
File: `src/puckling/dimensions/_registry.py`.

### RANK 3 — `tokens_by_start: dict[int, list[Token]]` index per saturation pass  *(−7 to −12% on long inputs)*
Replaces `for tok in tokens: if tok.range.start == pos` linear scan in the predicate-matching path with O(1) average. Index is rebuilt once per saturation iteration before the rule loop.
File: `src/puckling/engine.py`.

### RANK 6+2 — Precompute per-pattern matcher closures  *(−4 to −7%)*
`@cache`-d `_matchers_for_pattern(pattern)` builds one specialized closure per pattern slot at first use. Drops 2.3M `isinstance` calls per long parse. The closure captures the compiled regex or predicate `fn` directly, avoiding the dispatch on every probe.
File: `src/puckling/engine.py`.

### RANK 4 — Specialize single-item patterns  *(−9 to −18%)*
Most rules have a single-item pattern. Specialized path in `_apply_rule` skips `_match_pattern_from`'s recursion + tuple-splat entirely.
File: `src/puckling/engine.py`.

### RANK 5 — `regex.finditer(text, overlapped=True)` for single-item regex rules  *(−25 to −65%, biggest single win)*
For rules whose only item is a regex, drives the rule with **one** `finditer` C-side scan instead of `n+1` per-position `regex.match` calls. Equivalent semantics (verified by test suite). Single-item predicate rules also got a free win — they now iterate only positions present in `tokens_by_start` instead of every text position.
File: `src/puckling/engine.py`.

## What was NOT worth doing

cProfile evidence ruled out:
- `dataclasses.replace()` — 0.4% of cumtime (not the 6% I'd guessed).
- `_token_key` dedup tuple build — not in top 30.
- `_resolve_value` / `getattr` for resolution — 0.8%.
- `time.monotonic()` after the rule-boundary-only check — 0.3%.

## Side notes

- All 1,989 tests still pass. No xfail movement.
- The `finditer(overlapped=True)` path requires the `regex` package (already a dependency). `re` stdlib does not support overlapped iteration.
- Bench JSON snapshots in `bench/results/` show the per-step deltas if you want the granular history.
