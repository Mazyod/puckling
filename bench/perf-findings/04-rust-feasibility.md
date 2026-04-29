# Phase 3 — Rust extension feasibility

Originally explored on the `perf/rust-feasibility` branch (since retired). Baseline of comparison: phase-1 already-shipped (12.55 ms on `en/multi/long`).

User's GO bar (verbatim): **"a rust-based implementation that we should only ever consider if the performance reaches almost an order of magnitude faster or more."** Interpreted as ≥10× whole-parse speedup vs phase-1.

## TL;DR — NO-GO

Best-evidence projected whole-parse speedup of porting `_apply_rule`/`_match_pattern_from`/`_match_item_at` to Rust+PyO3 while keeping rules/predicates/productions in Python: **~3× over phase-1, ~7× over original `main`**.

Below the 10× bar by a factor of ~3. Phase-1's pure-Python micro-opts already captured the bulk of the available win at zero distribution cost.

## 1. Realistic speedup ceiling (Amdahl)

Profile data: `bench/results/20260428T162536Z-cprofile.cprof` (post-phase-1, 140 parses, 2.166 s).

| Frame | tottime | % of amortized total |
|---|---:|---:|
| `_match_item_at` body | 0.520s | 26.6% |
| `_regex.Pattern.match` (C call) | 0.484s | 24.8% |
| `_match_pattern_from` body | 0.436s | 22.3% |
| `_apply_rule` body | 0.292s | 14.9% |
| Engine glue (`isinstance` + `len` + `time.monotonic` + `_skip_whitespace`) | 0.125s | 6.4% |
| **Hot-loop subtotal (portable to Rust)** | **1.861s** | **95.2%** |
| Python tail (productions, value resolution, time helpers) | 0.094s | 4.8% |

Naive Amdahl looks tempting (10× hot-loop = 7× whole; 20× = 10×) — but the naive number assumes the entire 95% block goes Rust-native at speed X. **It can't:**

**(a) The regex C call (24.8% of total) won't speed up much.** The Python `regex` package is already a tuned C extension. Microbench against `google-re2` (an algorithmic peer of Rust's `regex` crate: linear-time, no lookarounds, both C-level):

```
pattern              len   regex(ms)   re(ms)   re2(ms)   regex-vs-re2
ar_fraction_NOLB      56        74.4     29.4     262.0   regex 3.5x FASTER
en_words              96       105.3     71.7     413.4   regex 3.9x FASTER
en_time               96       110.9     38.1     488.1   regex 4.4x FASTER
digits                96        89.6     40.4     473.6   regex 5.3x FASTER
```

For puckling's pattern shape (short Unicode strings, ~50–100 chars, called via `match()` at every text position), Python's `regex` C extension is already 3–5× faster than RE2-class engines. Rust's `regex` crate is somewhat faster than RE2 on long-string scanning but per-match overhead at this size is dominated by FFI marshalling, not engine cost. **Realistic ceiling for the regex.match component: 2–3×, not 10×.**

**(b) PyO3 callbacks for predicate items destroy part of the win.** Of 2.31M `_match_item_at` calls in the corpus, **445,820 (19.3%) are predicate-path** (`is_time(token)` etc.). Productions fire at every successful pattern match, also Python. PyO3 round-trip cost is ~0.5–2 µs per call (well-documented). At 1 µs:

- Predicate callbacks: 446K × 1µs = **0.45s of pure callback overhead** across the 140-parse corpus = ~3.2 ms/parse added to long inputs.

Per-parse projection on `en/multi/long` (12.55 ms post-phase-1):

| Component | Now | Rust port | Notes |
|---|---:|---:|---|
| regex C call (22%) | 2.76 ms | 1.10 ms | Rust `regex` ~2.5× over `regex` for these patterns |
| Pure Python loop (60%) | 7.53 ms | 0.15 ms | Rust effectively free here |
| Predicate path (18%) | 2.26 ms | 2.86 ms | Same Python work + PyO3 callback overhead |
| **Total** | **12.55 ms** | **~4.1 ms** | **3.05× over phase-1, 6.8× over original `main`** |

Below the 10× bar.

## 2. Compatibility blockers

**SEVERE — Lookbehind/lookahead used in 14 patterns across 6 files.** Rust `regex` crate explicitly forbids lookarounds (its linear-time guarantee). Affected files:
- `dimensions/credit_card/rules.py` — `(?<!\d)`, `(?!\d)`, alternation negative-lookaheads on card brands.
- `dimensions/amount_of_money/en/rules.py` — `(?<![A-Za-z])`, `(?![A-Za-z])`.
- `dimensions/numeral/en/rules.py` — `(?=[\W$€¢£]|$)`, `(?!\s*-)`.
- `dimensions/quantity/ar/rules.py` — `(?<![\p{L}\p{N}])`, `(?![\p{L}\p{N}])`.
- `dimensions/time/en/rules.py` and `clock_rules.py` — `(?!\d|\s*[/\-]\s*\d)`, AMPM `(?![A-Za-z])`.

These prevent runaway matching ("10am" matching as "10a" + "m", "$10k" matching "10" + "k", etc.). Workarounds:
1. Rewrite each pattern with anchored alternation + post-match validation in the production. Per-pattern engineering work, regression risk on 1989 tests.
2. Use the `fancy-regex` Rust crate which adds lookarounds but **drops the linear-time guarantee** — algorithmically the same complexity class as Python's `regex`, defeating the purpose.
3. Two-engine dispatch: send lookbehind patterns to Python `regex`, the rest to Rust. Now you maintain the FFI plus pattern classification plus the Python regex dependency anyway.

Estimate: 1–2 person-weeks just for pattern rewrites with regression hardening.

**MODERATE — Predicate functions are Python closures.** Calling them from Rust requires PyO3 callbacks. Already accounted for above (~3 ms/parse on long inputs).

**LOW — Closure-bearing token values.** Phase-2 found these break sub-interpreter pickling. **Not a problem for Rust** since the closure stays on the Python `Token` and the engine just shuttles object references through Rust without inspecting them.

**LOW — Unicode property classes.** Both engines support `\p{L}\p{N}` and Arabic-Indic digit ranges. No blocker.

## 3. Build / distribution complexity

Today (`pyproject.toml`): pure-Python wheels, single `hatchling` build, one dependency (`regex`). `pip install puckling` works on every platform with Python 3.13.

After Rust extension:
- Switch to `maturin` or `setuptools-rust` (replaces `hatchling`).
- Build wheels per: `linux-x86_64`, `linux-aarch64`, `linux-x86_64-musl`, `linux-aarch64-musl`, `macos-arm64`, `macos-x86_64`, `windows-x86_64`. **Seven wheel targets versus one.** Source distribution still needs a Rust toolchain at install time on unsupported targets.
- CI: GitHub Actions matrix expands ~7×. Add `cargo build --release`. Add `cibuildwheel` or `maturin-action`.
- `Cargo.lock`, `Cargo.toml`, `src/lib.rs`, FFI signatures synchronized with `src/puckling/types.py` — every rule-engine change is a 2-language change with FFI re-validation.
- ABI compatibility (PyO3 abi3 helps but constrains feature use).
- Debugging: stack traces straddle Rust/Python; reviewers need Rust fluency.

Maintenance overhead is permanent and proportional to engine churn.

## 4. Reference points from the wild

- **orjson vs stdlib json**: 2–10× on encode. **Leaf** task (no callbacks back to Python) — puckling's hot loop has callbacks.
- **polars vs pandas**: 5–30× on query workloads — vectorized columnar against contiguous memory, utterly different shape from puckling.
- **`google-re2` vs Python `regex`** (measured above): RE2 is **slower** for puckling's pattern shapes. The most-relevant reference and it's negative for the Rust premise.
- **No published Rust port of Duckling or equivalent NL parser exists** that we could find. The original Haskell Duckling was rewritten to optimize compile times, not to PyO3-bind. Absence isn't proof of impossibility but suggests the rewrite economics haven't favored anyone for this exact problem shape.

## 5. Recommendation — NO-GO

Projected whole-parse speedup of a Rust hot-loop port: ~3× over phase-1 / ~7× over original `main`. **Bar = 10× over phase-1.** Bar unmeetable because:

1. ~25% of post-phase-1 hot-loop time is C-level regex work where Rust isn't 10× faster on these patterns (RE2 is 2–5× *slower* in the head-to-head measured above).
2. ~19% of `_match_item_at` calls are Python-predicate callbacks that must FFI back via PyO3, eroding ~0.6 ms/parse of the win.
3. 14 patterns across 6 files use lookarounds that the Rust `regex` crate categorically rejects, requiring per-pattern semantic rewrites with regression risk on 1989 tests.

Cost side is heavy: ~3-4 person-weeks for the Rust core, ~1-2 for pattern rewrites, ~1 for CI/wheels, plus permanent FFI-synced maintenance overhead. **~6–8 person-weeks one-time + ongoing 2× engineering tax** for ~8 ms/parse savings on the slowest input that already runs in 12.55 ms post-phase-1.

**Park Rust** until either (a) puckling's hot loop becomes >100 ms on production inputs, (b) PyO3 callback cost drops by an order of magnitude, or (c) puckling's grammar can be expressed without predicates (so the entire engine can run regex-native), at which point the predicate-FFI tax in section 1.b evaporates.

## Files referenced

- `src/puckling/engine.py`, `src/puckling/types.py`, `src/puckling/dimensions/*/rules.py`
- `bench/results/20260428T162536Z-cprofile.cprof` — post-phase-1, 140 parses, 2.166s (used for Amdahl breakdown)
- `bench/results/20260428T134112Z-cprofile.cprof` — pre-phase-1 cross-check
- Pattern lookbehind sites: `dimensions/credit_card/rules.py`, `dimensions/amount_of_money/en/rules.py`, `dimensions/numeral/en/rules.py`, `dimensions/quantity/ar/rules.py`, `dimensions/time/en/rules.py`, `dimensions/time/en/clock_rules.py`
