# Performance ceiling exploration — summary

Autonomous follow-up to the bench-harness work on 2026-04-28. Three independent exploration branches isolating one performance lever each, plus a follow-up round on the winner. All branch code has since been consolidated into `main` and the branches retired; the per-phase findings live alongside this README. This document is the index.

## Starting state

- NLU service was observing **10–30 ms mean** wall time per `puckling.parse()` call (post-StopWatch measurement, sequential, no concurrency).
- User's gut SLA: **~5 ms**.
- Bench corpus: 28 cells, bilingual EN/AR, mirrors `Locale(lang, Region.KW)` + 7-dim filter exactly as the NLU integration uses it.
- Initial single fix already on `main` (commit `70c5426`): drop per-position `time.monotonic()` deadline check → **−10% on every cell**.

After that fix, `en/multi/long` baseline = **27.97 ms**, mean across corpus = ~7 ms.

## The three branches

### Phase 1 — `perf/python-micro-opts` — VERDICT: SHIPPED (v0.2.0)

Five targeted Python optimizations (see [`01-python-micro-opts.md`](01-python-micro-opts.md) for the per-rank breakdown):

1. `@functools.cache` on `_registry.rules_for(lang, dims)` — ~10% on long, up to 70% on shorts.
2. Token-by-start index, rebuilt once per saturation pass — O(1) predicate matching.
3. Precomputed per-pattern matcher closures — drops 2.3M `isinstance` calls.
4. Specialize single-item patterns — skips `_match_pattern_from` recursion.
5. `regex.finditer(text, overlapped=True)` for single-item regex rules — replaces n+1 anchored `match()` calls with one C-side scan.

Headline result on `en/multi/long`: **27.97 ms → 12.55 ms (−55%).** Mean improvement across the 28-cell corpus: 47–86%, every cell better. All 1,989 tests still pass.

### Round 2 — engine optimizations — VERDICT: SHIPPED (post-v0.2.0)

Three further engine-level changes on top of Phase 1 (see [`02-round-2-engine-opts.md`](02-round-2-engine-opts.md)):

1. **Text-only rule scheduling** — rules whose pattern is all-`RegexItem` run only on iteration 0 of saturation; they cannot observe new tokens, so subsequent passes only re-produce dedup-rejected work. Largest of the three wins.
2. **Parse-local anchored-regex memo** — multi-item regex matchers cache `compiled.match(text, pos=...)` within one `parse_and_resolve` call, cutting anchored regex calls ~82%.
3. **Exact-dimension predicate fast path** — predicates marked with an `__puckling_exact_dim__` attribute (e.g. `is_numeral`, `is_time`, `is_dim(x)`) specialize to a direct `tok.dim == dim` check.

Headline result on `en/multi/long`: **12.55 ms → 6.70 ms (−47%)**, ~76% cumulative reduction from the original `main` baseline. All tests still pass.

### Phase 2 — `perf/sub-interpreters` — VERDICT: KILLED

Investigated PEP 734 sub-interpreters AND PEP 703 free-threaded Python.

- **Sub-interpreters dead:** the `regex` C extension refuses own-GIL sub-interps; the workaround config (`isolated + use_main_obmalloc=True`) deadlocks; the only working config (`legacy`) shares the GIL so there's no actual parallelism. Plus closure-bearing time-rule values don't pickle. 4-worker prototype actually ran **3.6× SLOWER** than serial. Theoretical best case ~1.6× for ~3 person-months of substrate engineering.
- **Free-threaded Python tepid:** correctness verified (token sets bit-equal), but contention on `regex` library internals + Python allocator caps the practical speedup at ~1.2×. **2 workers gave only −14%**, 4+ workers regressed below serial.

Both substrate paths fall short of phase-1's 55% gain.

### Phase 3 — `perf/rust-feasibility` — VERDICT: PARKED

Researched a PyO3 port of `_apply_rule`/`_match_pattern_from`/`_match_item_at`, with realistic Amdahl based on profile data and a head-to-head regex microbench.

Best-case projection for `en/multi/long`: **12.55 ms → ~4.1 ms** (≈ 3× over phase-1, ≈ 7× over original `main`). User's bar (verbatim): "almost an order of magnitude faster or more" — interpreted as ≥10× over phase-1. **Bar missed by a factor of 3** because:

1. ~25% of post-phase-1 time is in the `regex` C engine (Python's `regex` package is *already* 3–5× faster than RE2-class engines on puckling's short-Unicode patterns).
2. ~19% of `_match_item_at` calls are Python-predicate callbacks → must FFI back via PyO3 (~1 µs each), erasing ~0.6 ms/parse.
3. 14 lookbehind/lookahead patterns across 6 files would need semantic rewrites — Rust's `regex` crate categorically refuses lookarounds.

Cost: ~6–8 person-weeks one-time + ongoing 2× engineering tax + 7-platform wheel matrix in CI vs current single pure-Python wheel. Not justified for ~8 ms/parse on one cell.

## Outcome

1. **Phase 1 shipped** as v0.2.0 — `en/multi/long` 27.97 ms → 12.55 ms.
2. **Round 2 shipped** post-v0.2.0 — `en/multi/long` 12.55 ms → 6.70 ms (~76% cumulative reduction from the original baseline).
3. **Sub-interpreter and Rust paths parked** as documented dead-ends so we don't re-litigate.
4. If `en/multi/long` (now 6.70 ms) becomes a hard ceiling for the SLA, the next levers are *not* parallelism or Rust — they are: (a) caching repeat utterances at the NLU layer (banking traffic is famously repetitive — likely a >2× practical win on real traffic at near-zero engineering cost), or (b) splitting the `time` dimension internally (it's 242 of 290 EN rules and dominates long-input cost).

## Where to read more

| Doc | File |
|---|---|
| Phase 1 — Python micro-opts (shipped) | [`01-python-micro-opts.md`](01-python-micro-opts.md) |
| Round 2 — engine optimizations (shipped) | [`02-round-2-engine-opts.md`](02-round-2-engine-opts.md) |
| Phase 2 — sub-interpreters + free-threaded Python (killed) | [`03-sub-interpreters-and-free-threading.md`](03-sub-interpreters-and-free-threading.md) |
| Phase 3 — Rust extension feasibility (parked) | [`04-rust-feasibility.md`](04-rust-feasibility.md) |
| Bench harness + corpus + JSON history | [`bench/`](..) |
| Production NLU integration (the workload these numbers mirror) | `../nlu/pkgs/arena/arena/ml_models/puckling_entity_extractor_model.py` |
