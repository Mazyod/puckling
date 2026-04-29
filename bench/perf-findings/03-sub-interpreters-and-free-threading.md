# Phase 2 — Sub-interpreter / multi-threaded parallelism

Originally explored on the `perf/sub-interpreters` branch (since retired). Baseline: `bench/results/baseline-micro-opts.json` (post-deadline-fix `main`, before any phase-1 micro-opts).

## TL;DR

Both forms of intra-call rule parallelism investigated were **disappointing on Python 3.13**:

| Approach | Result | Verdict |
|---|---|---|
| Sub-interpreters (PEP 734) | 3.6× *slower* than serial | **dead** |
| Free-threaded Python (PEP 703) | 14% faster with 2 workers; slower with 4+ | marginal lever |

For comparison, phase 1's pure-Python micro-opts on the same baseline cut the same long-input case by 55%. Parallelism adds cost and complexity for less gain than careful sequential code.

## Path A: Sub-interpreters (PEP 734)

Investigated via `interpreters-pep-734==0.5.0` backport and direct `_interpreters` / `_interpqueues` stdlib modules.

**Three independent substrate-level blockers, each fatal:**

1. **`regex` C extension refuses own-GIL sub-interpreters.**
   - Single-phase init module: `ImportError: module _regex does not support loading in subinterpreters`.
   - Affects every `RegexItem.__post_init__()` at `src/puckling/types.py:66` (every regex-bearing rule, ~290 rules out of ~290).

2. **Workaround config (`isolated + use_main_obmalloc=True + check_multi_interp_extensions=False`) deadlocks** on two concurrent OS threads calling `_interpreters.exec`. Reproducible with a trivial `time.sleep(0.1)` script. Likely a CPython 3.13 bug.

3. **The only working config (`legacy`) shares the main GIL.** No actual parallelism — sub-interps serialize on the same GIL.

**Measured numbers** (290-rule full PROD_DIMS not measurable due to (1) and (4) below; comparable cell is "PROD_DIMS minus time", 48 rules):

| Config | Mean | p50 | p95 | p99 |
|---|---:|---:|---:|---:|
| Serial (48 rules, no time) | 3.94ms | 3.93 | 4.07 | 4.22 |
| 4-worker sub-interp (legacy/shared-GIL) | **14.46ms** | 14.39 | 15.72 | 16.03 |

Per-iteration breakdown for the 4-worker run: 3 saturation iterations × 4 workers = 12 round trips; per-RT cost 1.54 ms (vs a measured 75 µs noop sub-interp round-trip floor); total ~18 ms of pure pickle/GIL-handoff overhead per parse against a 4 ms compute baseline.

**Plus a fourth blocker:**

4. **Closure-bearing `value` types don't pickle.** `RelTime.compute` and similar in `src/puckling/dimensions/time/en/_helpers.py:158` are closures captured by reducer functions on time tokens. 10/29 tokens on the test input are time tokens. Stripping `time` drops the rule set 290→48 and excludes 84% of the corpus's actual cost.

**Theoretical best-case ceiling**, even if all four blockers were fixed:
- 4-way perfect parallelism on the 26.7ms serial baseline: 6.7ms compute per worker
- Plus per-iteration round-trip cost (best plausible 75µs × 12 = 0.9ms)
- **~17ms total = 0.64× serial ≈ 1.6× speedup**

For ~3 months of engineering (replacing `regex` with stdlib `re` (loses Unicode property classes — would break Arabic), rewriting all closure-based time/holiday values, fixing the obmalloc deadlock upstream).

**Correctness sanity check:** with rules partitioned round-robin across 4 sub-interps and main-thread merge using `_token_key`, the produced token set is bit-identical to the serial path. The architecture is sound; the substrate isn't ready.

**Decision: kill.**

## Path B: Free-threaded Python (PEP 703)

Pivot suggestion from the sub-interpreter dead-end. Same `_apply_rule` parallelism via stdlib `threading.Thread` + `concurrent.futures.ThreadPoolExecutor`, no pickling, runs against the unmodified engine.

Set up via `uv python install 3.13t` (free-threaded CPython 3.13.13 build, GIL disabled by default).

**Benchmark** on the slowest cell (`"transfer 100 KWD to account 1234567 by tomorrow 5pm"`):

| Path | Mean | p50 | p95 | p99 |
|---|---:|---:|---:|---:|
| Serial `parse()` | 32.76ms | 32.72 | 33.36 | 33.72 |
| Serial engine only | 32.02ms | 31.90 | 32.86 | 33.15 |
| Parallel, 2 workers | **28.20ms** | 27.44 | 33.37 | 34.31 |
| Parallel, 4 workers | 32.09ms | 31.67 | 36.76 | 43.59 |
| Parallel, 8 workers | 64.60ms | 64.58 | 66.93 | 67.67 |

**Correctness:** 4-worker parallel produces a bit-identical token set to serial (29 unique tokens, sets equal). The architecture works.

**The win is small and bounded.** 2 workers shave ~14%. 4+ workers regress because the thread coordination overhead (ThreadPoolExecutor.submit + Future.result, plus contention on the `regex` package's internal state and Python's allocator under multi-threaded load) outweighs the parallel compute gain. Without GIL contention, but *with* allocator and library-internal contention, the practical speedup ceiling on this engine is ~1.2×.

**Decision: park.** Not worth deploying a free-threaded build of Python in production for 14%, especially since:
- 3.13t is "experimental" (still has rough edges in some C extensions; `regex` works but performance characteristics are subtle)
- Phase 1's micro-opts deliver 5× more improvement on the same input with no runtime change required.
- Thread-pool overhead amortizes badly for parses already in single-digit ms (everything except long EN multi after phase 1).

## Conclusion

After investigating both PEP 734 (sub-interpreters) and PEP 703 (free-threading), **intra-call parallelism is not the right lever for puckling on Python 3.13**. The combination of (a) the `regex` C extension's substrate quirks, (b) closure-bearing value types in the time dimension, and (c) library-internal contention even when the GIL is gone, caps the realistic speedup at ~1.2–1.6× and demands either deeply complex engineering or a non-default Python runtime.

Recommendation: rely on the phase-1 micro-opts for the bulk of the win, and explore phase 3 (Rust extension) only if a single-digit-ms ceiling on long inputs is non-negotiable.

## Reproducing

The prototypes were one-off scratch scripts and were not shipped (sub-interpreter route is dead, see substrate blockers above). The dependencies needed to retry the investigation:

- `interpreters-pep-734>=0.5.0` (PEP 734 backport) for sub-interpreter pools.
- CPython 3.13t (free-threaded build, `Py_GIL_DISABLED=1`) for the PEP 703 path.

The round-trip floor microbench just submits a no-op via `InterpreterPoolExecutor` and times it; reproducing only requires the backport package above.
