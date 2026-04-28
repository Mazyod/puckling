"""Per-call samples and aggregation. Stdlib only."""

from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PerCall:
    """One measured `parse()` call.

    All times in nanoseconds; counters are deltas observed during the call.
    """

    wall_ns: int
    cpu_ns: int
    voluntary_ctx_switches: int
    involuntary_ctx_switches: int
    minor_page_faults: int
    major_page_faults: int
    gc_gen0: int
    gc_gen1: int
    gc_gen2: int


@dataclass(frozen=True, slots=True)
class ColdMeasurement:
    """First measured call for a sample, before any warmup."""

    wall_ns: int
    cpu_ns: int


@dataclass(frozen=True, slots=True)
class Aggregate:
    """Stats over a list of `PerCall` samples.

    Times in microseconds for human readability. Counter fields are totals
    summed across all calls in the cell — easier to reason about than means
    when most calls have zero collections / zero faults.

    `cold_wall_us` / `cold_cpu_us` are the *single* first call before warmup
    for this sample; they're not a distribution.
    """

    n: int
    wall_mean_us: float
    wall_p50_us: float
    wall_p95_us: float
    wall_p99_us: float
    wall_min_us: float
    wall_max_us: float
    wall_stddev_us: float
    cpu_mean_us: float
    voluntary_ctx_switches_total: int
    involuntary_ctx_switches_total: int
    minor_page_faults_total: int
    major_page_faults_total: int
    gc_gen0_total: int
    gc_gen1_total: int
    gc_gen2_total: int
    cold_wall_us: float
    cold_cpu_us: float


def _percentile(sorted_xs: list[float], p: float) -> float:
    """Linear-interpolated percentile. `p` is in [0, 100]."""
    if not sorted_xs:
        return 0.0
    if len(sorted_xs) == 1:
        return sorted_xs[0]
    rank = (p / 100.0) * (len(sorted_xs) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_xs) - 1)
    frac = rank - lo
    return sorted_xs[lo] * (1 - frac) + sorted_xs[hi] * frac


def aggregate(calls: list[PerCall], cold: ColdMeasurement | None) -> Aggregate:
    cold_wall = (cold.wall_ns / 1_000.0) if cold else 0.0
    cold_cpu = (cold.cpu_ns / 1_000.0) if cold else 0.0

    if not calls:
        return Aggregate(
            n=0,
            wall_mean_us=0.0,
            wall_p50_us=0.0,
            wall_p95_us=0.0,
            wall_p99_us=0.0,
            wall_min_us=0.0,
            wall_max_us=0.0,
            wall_stddev_us=0.0,
            cpu_mean_us=0.0,
            voluntary_ctx_switches_total=0,
            involuntary_ctx_switches_total=0,
            minor_page_faults_total=0,
            major_page_faults_total=0,
            gc_gen0_total=0,
            gc_gen1_total=0,
            gc_gen2_total=0,
            cold_wall_us=cold_wall,
            cold_cpu_us=cold_cpu,
        )

    walls_us = sorted(c.wall_ns / 1_000.0 for c in calls)
    cpus_us = [c.cpu_ns / 1_000.0 for c in calls]

    return Aggregate(
        n=len(calls),
        wall_mean_us=statistics.fmean(walls_us),
        wall_p50_us=_percentile(walls_us, 50),
        wall_p95_us=_percentile(walls_us, 95),
        wall_p99_us=_percentile(walls_us, 99),
        wall_min_us=walls_us[0],
        wall_max_us=walls_us[-1],
        wall_stddev_us=statistics.pstdev(walls_us) if len(walls_us) > 1 else 0.0,
        cpu_mean_us=statistics.fmean(cpus_us),
        voluntary_ctx_switches_total=sum(c.voluntary_ctx_switches for c in calls),
        involuntary_ctx_switches_total=sum(c.involuntary_ctx_switches for c in calls),
        minor_page_faults_total=sum(c.minor_page_faults for c in calls),
        major_page_faults_total=sum(c.major_page_faults for c in calls),
        gc_gen0_total=sum(c.gc_gen0 for c in calls),
        gc_gen1_total=sum(c.gc_gen1 for c in calls),
        gc_gen2_total=sum(c.gc_gen2 for c in calls),
        cold_wall_us=cold_wall,
        cold_cpu_us=cold_cpu,
    )
