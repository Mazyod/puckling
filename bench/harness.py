"""Measurement loop.

For each sample in the (possibly filtered) corpus:
- Build `Context` and `Options` outside the timed region (mirrors NLU prod).
- Time a single *cold* call (first call after registry warmup) before any
  per-sample warmup. Useful for spotting registry/import overhead.
- Run `warmup` calls and discard them.
- Run `rounds` calls, sampling wall + CPU time and OS/GC counter deltas.

Production config we mirror (verified at
`../nlu/pkgs/arena/arena/ml_models/puckling_entity_extractor_model.py:90-99`):

    Locale(lang, Region.KW)
    Options(parse_timeout_ms=3000)
    dims = ("amount_of_money", "duration", "email", "ordinal",
            "phone_number", "time", "url")

`run_bench` accepts `dims` and `filter_substr` so we can compare the
production configuration against alternatives (full 13-dim, single-dim,
subset by tag).
"""

from __future__ import annotations

import datetime as dt
import gc
import resource
import time
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from puckling import Context, Locale, Options, Region, parse

from bench.corpus import CORPUS, Sample, length_bucket
from bench.metrics import Aggregate, ColdMeasurement, PerCall, aggregate

PROD_DIMS = (
    "amount_of_money",
    "duration",
    "email",
    "ordinal",
    "phone_number",
    "time",
    "url",
)
PROD_REGION = Region.KW
PROD_TIMEOUT_MS = 3000
PROD_TZ = ZoneInfo("Asia/Kuwait")


@dataclass(frozen=True, slots=True)
class CellResult:
    sample: Sample
    bucket: str
    agg: Aggregate


@dataclass(frozen=True, slots=True)
class RunResult:
    rounds: int
    warmup: int
    dims: tuple[str, ...] | None  # None = no filter (all dims)
    cells: tuple[CellResult, ...]


def _gc_collections() -> tuple[int, int, int]:
    s = gc.get_stats()
    return (s[0]["collections"], s[1]["collections"], s[2]["collections"])


def _select_corpus(filter_substr: str | None) -> tuple[Sample, ...]:
    if not filter_substr:
        return CORPUS
    return tuple(s for s in CORPUS if filter_substr in s.tag)


def _measure_sample(
    sample: Sample,
    *,
    warmup: int,
    rounds: int,
    dims: tuple[str, ...] | None,
) -> tuple[ColdMeasurement, list[PerCall]]:
    options = Options(parse_timeout_ms=PROD_TIMEOUT_MS)
    locale = Locale(sample.lang, PROD_REGION)

    # Cold: first call for this sample, before any warmup. Captures any
    # per-sample lazy-load cost (e.g. regex compilation if not already cached).
    ctx = Context(reference_time=dt.datetime.now(tz=PROD_TZ), locale=locale)
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    parse(sample.text, ctx, options, dims=dims)
    cpu_end = time.process_time_ns()
    wall_end = time.perf_counter_ns()
    cold = ColdMeasurement(wall_ns=wall_end - wall_start, cpu_ns=cpu_end - cpu_start)

    # Warmup
    for _ in range(warmup):
        ctx = Context(reference_time=dt.datetime.now(tz=PROD_TZ), locale=locale)
        parse(sample.text, ctx, options, dims=dims)

    # Hot loop
    calls: list[PerCall] = []
    for _ in range(rounds):
        ctx = Context(reference_time=dt.datetime.now(tz=PROD_TZ), locale=locale)

        ru0 = resource.getrusage(resource.RUSAGE_SELF)
        gc0 = _gc_collections()
        wall_start = time.perf_counter_ns()
        cpu_start = time.process_time_ns()

        parse(sample.text, ctx, options, dims=dims)

        cpu_end = time.process_time_ns()
        wall_end = time.perf_counter_ns()
        gc1 = _gc_collections()
        ru1 = resource.getrusage(resource.RUSAGE_SELF)

        calls.append(
            PerCall(
                wall_ns=wall_end - wall_start,
                cpu_ns=cpu_end - cpu_start,
                voluntary_ctx_switches=ru1.ru_nvcsw - ru0.ru_nvcsw,
                involuntary_ctx_switches=ru1.ru_nivcsw - ru0.ru_nivcsw,
                minor_page_faults=ru1.ru_minflt - ru0.ru_minflt,
                major_page_faults=ru1.ru_majflt - ru0.ru_majflt,
                gc_gen0=gc1[0] - gc0[0],
                gc_gen1=gc1[1] - gc0[1],
                gc_gen2=gc1[2] - gc0[2],
            )
        )

    return cold, calls


def run_bench(
    *,
    warmup: int = 10,
    rounds: int = 200,
    dims: tuple[str, ...] | None = PROD_DIMS,
    filter_substr: str | None = None,
) -> RunResult:
    cells: list[CellResult] = []
    for sample in _select_corpus(filter_substr):
        cold, calls = _measure_sample(sample, warmup=warmup, rounds=rounds, dims=dims)
        cells.append(
            CellResult(
                sample=sample,
                bucket=length_bucket(sample),
                agg=aggregate(calls, cold),
            )
        )
    return RunResult(rounds=rounds, warmup=warmup, dims=dims, cells=tuple(cells))
