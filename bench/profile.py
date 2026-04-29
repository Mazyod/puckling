"""Profiling drill-downs.

Two modes, both kept separate from `run` because the instrumentation has
non-trivial overhead and would distort the timing numbers:

- `cprofile`: deterministic function-level profiler. Top hot functions by
  cumulative time across the whole corpus. Writes a `.cprof` artifact for
  inspection in `snakeviz`, `gprof2dot`, etc.
- `tracemalloc`: tracks Python-level allocations. Top allocation sites by
  bytes / count. Pinpoints object churn.

Both replay the corpus through the same prod-shaped configuration as
`harness.run_bench`. They reuse the production constants so workload
divergence between modes is impossible.
"""

from __future__ import annotations

import cProfile
import datetime as dt
import io
import linecache
import pstats
import tracemalloc
from pathlib import Path

from bench.corpus import CORPUS
from bench.harness import PROD_DIMS, PROD_REGION, PROD_TIMEOUT_MS, PROD_TZ
from puckling import Context, Locale, Options, parse


def _exercise_corpus(*, rounds: int) -> None:
    """Replay the corpus N times. Identical config to `harness._measure_sample`."""
    options = Options(parse_timeout_ms=PROD_TIMEOUT_MS)
    for _ in range(rounds):
        for sample in CORPUS:
            ctx = Context(
                reference_time=dt.datetime.now(tz=PROD_TZ),
                locale=Locale(sample.lang, PROD_REGION),
            )
            parse(sample.text, ctx, options, dims=PROD_DIMS)


def run_cprofile(*, rounds: int, results_dir: Path, top_n: int) -> Path:
    """Profile the whole corpus N times, write .cprof, print top hot funcs."""
    results_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(tz=dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = results_dir / f"{ts}-cprofile.cprof"

    profiler = cProfile.Profile()
    # Warm up first so we don't profile module imports / regex compilation.
    _exercise_corpus(rounds=1)
    profiler.enable()
    _exercise_corpus(rounds=rounds)
    profiler.disable()
    profiler.dump_stats(str(out_path))

    print(f"\nTop {top_n} functions by cumulative time:")
    buf = io.StringIO()
    stats = pstats.Stats(profiler, stream=buf).sort_stats("cumulative")
    stats.print_stats(top_n)
    print(buf.getvalue())

    print(f"\nTop {top_n} functions by total time (self):")
    buf = io.StringIO()
    stats = pstats.Stats(profiler, stream=buf).sort_stats("tottime")
    stats.print_stats(top_n)
    print(buf.getvalue())

    print(f"Wrote {out_path}")
    print("Inspect interactively with:  uv run snakeviz", out_path)
    return out_path


def run_tracemalloc(*, rounds: int, top_n: int) -> None:
    """Trace allocations during corpus replay.

    Reports two views:
    - **Net retention** (snapshot diff): which sites have surviving objects.
      Indicates leaks / pinned references. Usually tiny for a parser.
    - **Peak memory** during the run: high-water mark. Indicates *churn* —
      how much memory the parser allocates mid-call before freeing. This is
      the proxy for "how much work is the allocator doing per parse".
    """
    # Warm up so we don't measure import-time allocs.
    _exercise_corpus(rounds=1)

    tracemalloc.start(25)
    tracemalloc.reset_peak()
    snap_before = tracemalloc.take_snapshot()
    cur_before, peak_before = tracemalloc.get_traced_memory()

    _exercise_corpus(rounds=rounds)

    snap_after = tracemalloc.take_snapshot()
    cur_after, peak_after = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    n_calls = rounds * len(CORPUS)
    print(f"\nTracemalloc summary across {n_calls} parse calls ({rounds} replays × {len(CORPUS)} samples):")
    print(f"  resident before:  {cur_before/1024:8.1f} KiB")
    print(f"  resident after:   {cur_after/1024:8.1f} KiB   (delta {((cur_after-cur_before)/1024):+.1f} KiB)")
    print(f"  peak during run:  {peak_after/1024:8.1f} KiB   (peak−before = {((peak_after-cur_before)/1024):+.1f} KiB; ~{((peak_after-cur_before)/n_calls):.0f} B/call high-water)")

    top_size = snap_after.compare_to(snap_before, "lineno")
    print(f"\nTop {top_n} retention sites (net bytes added between snapshots):")
    print(f"  {'bytes':>12}  {'count':>8}  location")
    for stat in top_size[:top_n]:
        frame = stat.traceback[0]
        line = linecache.getline(frame.filename, frame.lineno).strip()
        loc = f"{Path(frame.filename).name}:{frame.lineno}"
        print(f"  {stat.size_diff:>12}  {stat.count_diff:>8}  {loc}  |  {line[:80]}")
