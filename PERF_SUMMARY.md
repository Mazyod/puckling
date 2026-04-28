# Performance ceiling exploration — summary

Autonomous follow-up to the bench-harness work on 2026-04-28. Three independent branches, each with its own `PERF_FINDINGS.md` and code, isolating one performance lever per branch. This document is the index.

## Starting state

- NLU service was observing **10–30 ms mean** wall time per `puckling.parse()` call (post-StopWatch measurement, sequential, no concurrency).
- User's gut SLA: **~5 ms**.
- Bench corpus: 28 cells, bilingual EN/AR, mirrors `Locale(lang, Region.KW)` + 7-dim filter exactly as the NLU integration uses it.
- Initial single fix already on `main` (commit `70c5426`): drop per-position `time.monotonic()` deadline check → **−10% on every cell**.

After that fix, `en/multi/long` baseline = **27.97 ms**, mean across corpus = ~7 ms.

## The three branches

### `perf/python-micro-opts` — VERDICT: SHIP

Five targeted Python optimizations (see `git show perf/python-micro-opts:PERF_FINDINGS.md` for the per-rank breakdown):

1. `@functools.cache` on `_registry.rules_for(lang, dims)` — ~10% on long, up to 70% on shorts.
2. Token-by-start index, rebuilt once per saturation pass — O(1) predicate matching.
3. Precomputed per-pattern matcher closures — drops 2.3M `isinstance` calls.
4. Specialize single-item patterns — skips `_match_pattern_from` recursion.
5. `regex.finditer(text, overlapped=True)` for single-item regex rules — replaces n+1 anchored `match()` calls with one C-side scan.

Headline result on `en/multi/long`: **27.97 ms → 12.55 ms (−55%).** Mean improvement across the 28-cell corpus: 47–86%, every cell better. All 1,989 tests still pass.

### `perf/sub-interpreters` — VERDICT: KILL

Investigated PEP 734 sub-interpreters AND PEP 703 free-threaded Python.

- **Sub-interpreters dead:** the `regex` C extension refuses own-GIL sub-interps; the workaround config (`isolated + use_main_obmalloc=True`) deadlocks; the only working config (`legacy`) shares the GIL so there's no actual parallelism. Plus closure-bearing time-rule values don't pickle. 4-worker prototype actually ran **3.6× SLOWER** than serial. Theoretical best case ~1.6× for ~3 person-months of substrate engineering.
- **Free-threaded Python tepid:** correctness verified (token sets bit-equal), but contention on `regex` library internals + Python allocator caps the practical speedup at ~1.2×. **2 workers gave only −14%**, 4+ workers regressed below serial.

Both substrate paths fall short of phase-1's 55% gain.

### `perf/rust-feasibility` — VERDICT: PARK

Researched a PyO3 port of `_apply_rule`/`_match_pattern_from`/`_match_item_at`, with realistic Amdahl based on profile data and a head-to-head regex microbench.

Best-case projection for `en/multi/long`: **12.55 ms → ~4.1 ms** (≈ 3× over phase-1, ≈ 7× over original `main`). User's bar (verbatim): "almost an order of magnitude faster or more" — interpreted as ≥10× over phase-1. **Bar missed by a factor of 3** because:

1. ~25% of post-phase-1 time is in the `regex` C engine (Python's `regex` package is *already* 3–5× faster than RE2-class engines on puckling's short-Unicode patterns).
2. ~19% of `_match_item_at` calls are Python-predicate callbacks → must FFI back via PyO3 (~1 µs each), erasing ~0.6 ms/parse.
3. 14 lookbehind/lookahead patterns across 6 files would need semantic rewrites — Rust's `regex` crate categorically refuses lookarounds.

Cost: ~6–8 person-weeks one-time + ongoing 2× engineering tax + 7-platform wheel matrix in CI vs current single pure-Python wheel. Not justified for ~8 ms/parse on one cell.

## Recommendation

1. **Merge `perf/python-micro-opts` to main** as soon as possible. Zero distribution change, all tests pass, 47–86% latency cut across the bench corpus, every cell improved. After merge, `en/multi/long` = 12.55 ms; **27 of 28 cells under 5 ms**.
2. **Park sub-interpreter and Rust paths.** Both branches stay around as documented dead-ends so we don't re-litigate.
3. If the remaining slowest cell (`en/multi/long` at 12.55 ms) becomes a hard ceiling for the SLA, the next levers are *not* parallelism or Rust — they are: (a) caching repeat utterances at the NLU layer (banking traffic is famously repetitive — likely a >2× practical win on real traffic at near-zero engineering cost), or (b) splitting the `time` dimension internally (it's 242 of 290 EN rules and dominates long-input cost).

## Where to read more

| File | Where |
|---|---|
| Phase 1 changes + findings | `git checkout perf/python-micro-opts`, then `PERF_FINDINGS.md` |
| Phase 2 sub-interp + free-threaded findings | `git checkout perf/sub-interpreters`, then `PERF_FINDINGS.md` |
| Phase 3 Rust feasibility report | `git checkout perf/rust-feasibility`, then `PERF_FINDINGS.md` |
| Bench harness + corpus + JSON history | `bench/` on any branch (ships unchanged on `main`) |
| Production NLU integration (the workload these numbers mirror) | `../nlu/pkgs/arena/arena/ml_models/puckling_entity_extractor_model.py` |
