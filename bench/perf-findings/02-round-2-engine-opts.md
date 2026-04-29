# Round 2 performance findings

Date: 2026-04-28

Baseline: clean `a9e7144` (`main` after `perf/python-micro-opts`)
Candidate: this patch
Runtime: CPython 3.14.4, host benchmark, prod dim filter:
`amount_of_money,duration,email,ordinal,phone_number,time,url`

## Result

| Metric | Baseline | Candidate | Delta |
|---|---:|---:|---:|
| Overall weighted mean | 2.90 ms | 1.79 ms | -38.3% |
| EN weighted mean | 4.36 ms | 2.59 ms | -40.6% |
| AR weighted mean | 960 us | 724 us | -24.6% |
| Long bucket mean | 12.48 ms | 6.88 ms | -44.9% |
| Slowest cell: EN multi long | 12.48 ms | 6.88 ms | -44.9% |
| EN URL medium | 5.18 ms | 3.20 ms | -38.2% |
| EN email medium | 4.77 ms | 2.88 ms | -39.6% |
| AR multi long | 2.08 ms | 1.52 ms | -26.9% |

The full suite passes: `1991 passed, 2 xfailed`.

Profile movement over the same 560-parse cProfile workload:

| Profile counter | Baseline | Candidate | Delta |
|---|---:|---:|---:|
| Total profiler time | 3.857 s | 2.723 s | -29.4% |
| `_apply_rule` calls | 362,060 | 209,180 | -42.2% |
| Anchored regex `match()` calls | 2,532,160 | 459,980 | -81.8% |
| Single-regex `finditer()` calls | 204,960 | 75,280 | -63.3% |

## Shipped changes

### 1. Text-only rule scheduling

Rules whose patterns contain only `RegexItem` slots are now run only during the
first saturation pass. They cannot observe the evolving token forest, so later
passes only re-produce already-seen tokens. Token-dependent rules keep the
original fixed-point behavior.

Impact: this is the largest win. EN prod has 183 text-only rules out of 290;
AR has 123 out of 163. Expensive samples usually need 3-4 saturation passes,
so skipping repeated text-only work removes hundreds of rule applications per
call.

Maintenance overhead: low to moderate. The classification is conservative:
anything with a non-regex item remains token-dependent. The only semantic
caveat is for intentionally impure rule productions, which the project model
already disallows.

### 2. Parse-local anchored regex memo

Multi-item regex matchers now cache anchored `compiled.match(text, pos=...)`
results for the duration of one parse. Single-item regex rules still use the
existing overlapped `finditer()` fast path.

Impact: reduces repeated anchored regex calls across saturation passes. The
cache is parse-local and keyed by compiled-pattern identity plus position.

Maintenance overhead: moderate. The extra dict lookup can be overhead on
one-off probes, but the profile shows it pays back on the current rule set.
Memory is bounded by one parse's pattern-position probes.

### 3. Exact-dimension predicate fast path

Common predicates such as `is_numeral`, `is_time`, `is_duration`, `is_grain`,
and `is_dim(...)` carry private exact-dimension metadata. The engine can then
inline `tok.dim == dim` instead of calling the predicate function for every
candidate token. Predicates without metadata still use the generic path.

Impact: small but broad. It avoids Python callback overhead for the most common
cross-dimension predicates without changing rule definitions.

Maintenance overhead: low to moderate. It is a private convention between
`puckling.predicates` and the engine. A heavier per-start/per-dimension index
was tested and regressed, so it was not kept.

## Rejected or parked experiments

### 4. Iterative/unrolled multi-item matcher - rejected

Replacing the recursive matcher with length-specific nested loops and an
explicit stack preserved correctness in isolation, but regressed the key EN
benchmarks:

| Metric | Baseline | Experiment | Delta |
|---|---:|---:|---:|
| EN multi long | 13.11 ms | 13.63 ms | +4.0% |
| EN weighted | 4.51 ms | 4.73 ms | +4.9% |
| AR weighted | 987 us | 988 us | flat |

Maintenance overhead: high for no gain. It adds duplicated hot-path code and
more branching around pattern lengths.

### 5. Production no-hit prefilter - not shipped in the library

A conservative API-level trigger filter for the exact prod dim set can skip
obvious no-entity inputs:

| No-entity sample | Normal | Prefiltered |
|---|---:|---:|
| EN `hello` | 591 us | 2.9 us |
| EN medium no-entity | 2.09-2.46 ms | 12-18 us |
| AR no-entity | 139-498 us | 5-6 us |

It is very attractive for the NLU service if real traffic has many no-entity
utterances. It was not kept in `puckling.api` because it is a manual trigger
inventory and therefore can create false negatives when rules evolve. The
better place is a production wrapper with telemetry, a shadow-mode rollout,
and alerts for skipped phrases that later appear in labeled corpora.

Maintenance overhead: medium to high. The shortcut must stay synchronized with
every rule file and every future dimension expansion.

### 6. Rust core - parked

A thin PyO3/Rust core would mostly move `_apply_rule`, `_match_pattern_from`,
token indexing, and dedup scaffolding. It would not cleanly move Python
predicates, Python `Rule.prod` functions, Python value dataclasses, or time
resolution without turning the project into a full rewrite.

Expected upside is bounded. With the current profile, even an impossible
infinitely-fast engine hot loop caps whole-parse speedup at a few times over
this patch. A realistic PyO3 port is more likely to land around 2.5-3.2x on
the remaining engine cost, enough to push the slowest cell near 4-5 ms, but not
an order-of-magnitude gain.

Compatibility and packaging risks:

- Rust `regex` intentionally does not support look-around or backreferences:
  https://docs.rs/regex
- `fancy-regex` supports look-around/backreferences via backtracking, which
  weakens the main reason to move regex matching to Rust:
  https://docs.rs/fancy-regex/
- PyO3 distribution adds native wheels and platform CI:
  https://pyo3.rs/main/building-and-distribution.html

Maintenance overhead: high. A Rust core adds Rust toolchain ownership, PyO3
bindings, object conversion, and a wheel matrix, while still calling back into
Python for much of the rule semantics.

## Recommendation

Keep the shipped engine changes. They are still pure/functional at the parser
API boundary, preserve the fixed-point model for token-dependent rules, and
give a large win without changing distribution.

For another big production win, put the no-hit prefilter or an utterance-result
cache in the NLU layer rather than in the library core. That path can be
validated against real traffic and rolled back independently if a trigger miss
appears.
