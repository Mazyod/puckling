"""CLI entry: `python -m bench [run|profile] ...`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bench.compare import gate, load_run, print_diff
from bench.harness import PROD_DIMS, RunResult, run_bench
from bench.metrics import Aggregate
from bench.profile import run_cprofile, run_tracemalloc
from bench.report import write_json

RESULTS_DIR = Path(__file__).resolve().parent / "results"

# Convenience aliases for `--dims`. `prod` mirrors the NLU service's filter;
# `full` disables filtering (all 13 dimensions). Anything else is treated as
# a comma-separated list (e.g. `--dims time` or `--dims time,numeral`).
DIMS_ALIASES: dict[str, tuple[str, ...] | None] = {
    "prod": PROD_DIMS,
    "full": None,
}


def _parse_dims(arg: str) -> tuple[str, ...] | None:
    if arg in DIMS_ALIASES:
        return DIMS_ALIASES[arg]
    return tuple(d.strip() for d in arg.split(",") if d.strip())


def _fmt_us(us: float) -> str:
    if us >= 1000:
        return f"{us/1000:7.2f}ms"
    return f"{us:7.1f}µs"


def _truncate(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def _print_table(result: RunResult) -> None:
    cols = ("tag", "text", "cold", "mean", "p50", "p95", "p99", "stddev", "cold/mean")
    widths = (22, 32, 9, 9, 9, 9, 9, 9, 9)
    header = "  ".join(f"{c:<{w}}" for c, w in zip(cols, widths, strict=True))
    print(header)
    print("-" * len(header))

    for cell in result.cells:
        a: Aggregate = cell.agg
        cold_ratio = (a.cold_wall_us / a.wall_mean_us) if a.wall_mean_us else 0.0
        row = (
            cell.sample.tag,
            _truncate(cell.sample.text, widths[1]),
            _fmt_us(a.cold_wall_us),
            _fmt_us(a.wall_mean_us),
            _fmt_us(a.wall_p50_us),
            _fmt_us(a.wall_p95_us),
            _fmt_us(a.wall_p99_us),
            _fmt_us(a.wall_stddev_us),
            f"{cold_ratio:6.2f}x",
        )
        print("  ".join(f"{v:<{w}}" for v, w in zip(row, widths, strict=True)))


def _print_locale_summary(result: RunResult) -> None:
    print("\nBy locale (mean wall, weighted by call count):")
    by_lang: dict[str, tuple[float, int]] = {}
    for cell in result.cells:
        lang = cell.sample.lang.value
        cur_sum, cur_n = by_lang.get(lang, (0.0, 0))
        by_lang[lang] = (cur_sum + cell.agg.wall_mean_us * cell.agg.n, cur_n + cell.agg.n)
    for lang, (s, n) in sorted(by_lang.items()):
        if n:
            print(f"  {lang}: {_fmt_us(s / n)}  (n={n})")


def _print_bucket_summary(result: RunResult) -> None:
    print("\nBy length bucket (mean wall, weighted):")
    by_bucket: dict[str, tuple[float, int]] = {}
    for cell in result.cells:
        cur_sum, cur_n = by_bucket.get(cell.bucket, (0.0, 0))
        by_bucket[cell.bucket] = (cur_sum + cell.agg.wall_mean_us * cell.agg.n, cur_n + cell.agg.n)
    for bucket in ("short", "medium", "long"):
        if bucket not in by_bucket:
            continue
        s, n = by_bucket[bucket]
        if n:
            print(f"  {bucket:>6}: {_fmt_us(s / n)}  (n={n})")


def _print_overall_counters(result: RunResult) -> None:
    total_calls = sum(c.agg.n for c in result.cells)
    if not total_calls:
        return
    gc0 = sum(c.agg.gc_gen0_total for c in result.cells)
    gc1 = sum(c.agg.gc_gen1_total for c in result.cells)
    gc2 = sum(c.agg.gc_gen2_total for c in result.cells)
    iv = sum(c.agg.involuntary_ctx_switches_total for c in result.cells)
    vol = sum(c.agg.voluntary_ctx_switches_total for c in result.cells)
    minflt = sum(c.agg.minor_page_faults_total for c in result.cells)
    majflt = sum(c.agg.major_page_faults_total for c in result.cells)
    print(f"\nOverall counters across {total_calls} calls:")
    print(f"  gc collections     gen0={gc0}  gen1={gc1}  gen2={gc2}")
    print(f"  ctx switches       voluntary={vol}  involuntary={iv}")
    print(f"  page faults        minor={minflt}  major={majflt}")


def _print_cold_summary(result: RunResult) -> None:
    cold_total = sum(c.agg.cold_wall_us for c in result.cells)
    warm_total = sum(c.agg.wall_mean_us for c in result.cells)
    if not warm_total:
        return
    n = len(result.cells)
    print(
        f"\nCold-vs-warm: avg cold {_fmt_us(cold_total / n).strip()} "
        f"vs avg warm {_fmt_us(warm_total / n).strip()} "
        f"(ratio {cold_total / warm_total:.2f}x)"
    )


def _cmd_run(args: argparse.Namespace) -> int:
    dims = _parse_dims(args.dims)
    result = run_bench(
        warmup=args.warmup,
        rounds=args.rounds,
        dims=dims,
        filter_substr=args.filter,
    )
    dims_label = "full" if dims is None else (",".join(dims) if dims else "<empty>")
    print(
        f"warmup={result.warmup}  rounds={result.rounds}  "
        f"cells={len(result.cells)}  dims={dims_label}\n"
    )
    if not result.cells:
        print(f"(no samples matched filter {args.filter!r})")
        return 0
    _print_table(result)
    _print_locale_summary(result)
    _print_bucket_summary(result)
    _print_cold_summary(result)
    _print_overall_counters(result)
    if not args.no_json:
        path = write_json(result, RESULTS_DIR)
        print(f"\nWrote {path}")
    return 0


def _cmd_profile(args: argparse.Namespace) -> int:
    if args.kind == "cprofile":
        run_cprofile(rounds=args.rounds, results_dir=RESULTS_DIR, top_n=args.top_n)
    elif args.kind == "tracemalloc":
        run_tracemalloc(rounds=args.rounds, top_n=args.top_n)
    else:
        raise ValueError(f"unknown profile kind: {args.kind!r}")
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    a = load_run(Path(args.a))
    b = load_run(Path(args.b))
    print_diff(a, b)
    return 0


def _cmd_gate(args: argparse.Namespace) -> int:
    baseline = load_run(Path(args.baseline))
    candidate = load_run(Path(args.candidate))
    regressions = gate(
        baseline=baseline,
        candidate=candidate,
        tolerance_pct=args.tolerance_pct,
        field=args.field,
    )
    if not regressions:
        n = len(baseline["cells"])
        print(f"OK — no cell regressed by more than {args.tolerance_pct:.1f}% on {args.field} (across {n} cells).")
        return 0
    print(f"FAIL — {len(regressions)} cell(s) regressed by more than {args.tolerance_pct:.1f}% on {args.field}:")
    for d in regressions:
        pct = d.pct(args.field)
        a_us = d.a[args.field]
        b_us = d.b[args.field]
        a_str = f"{a_us/1000:.2f}ms" if a_us >= 1000 else f"{a_us:.0f}µs"
        b_str = f"{b_us/1000:.2f}ms" if b_us >= 1000 else f"{b_us:.0f}µs"
        print(f"  {d.tag:<22}  {d.text[:40]!r}  {a_str} → {b_str}  (+{pct:.1f}%)")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bench")
    sub = parser.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="run the benchmark and print a summary")
    p_run.add_argument("--warmup", type=int, default=10)
    p_run.add_argument("--rounds", type=int, default=200)
    p_run.add_argument(
        "--dims",
        default="prod",
        help="prod | full | comma-separated dim names (default: prod)",
    )
    p_run.add_argument("--filter", default=None, help="substring match on tag (e.g. 'en/' or 'multi')")
    p_run.add_argument("--no-json", action="store_true", help="skip writing results JSON")
    p_run.set_defaults(func=_cmd_run)

    p_prof = sub.add_parser("profile", help="profile the corpus (cprofile or tracemalloc)")
    p_prof.add_argument("kind", choices=("cprofile", "tracemalloc"))
    p_prof.add_argument("--rounds", type=int, default=10)
    p_prof.add_argument("--top-n", type=int, default=25)
    p_prof.set_defaults(func=_cmd_profile)

    p_cmp = sub.add_parser("compare", help="diff two run JSONs (no exit code)")
    p_cmp.add_argument("a", help="path to baseline JSON")
    p_cmp.add_argument("b", help="path to candidate JSON")
    p_cmp.set_defaults(func=_cmd_compare)

    p_gate = sub.add_parser("gate", help="exit non-zero if candidate regressed vs baseline")
    p_gate.add_argument("baseline", help="path to baseline JSON")
    p_gate.add_argument("candidate", help="path to candidate JSON")
    p_gate.add_argument(
        "--tolerance-pct",
        type=float,
        default=5.0,
        help="allowed regression in percent (default: 5.0)",
    )
    p_gate.add_argument(
        "--field",
        default="wall_mean_us",
        choices=("wall_mean_us", "wall_p50_us", "wall_p95_us", "wall_p99_us"),
        help="which metric to gate on (default: wall_mean_us)",
    )
    p_gate.set_defaults(func=_cmd_gate)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        args = parser.parse_args(["run"])
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
