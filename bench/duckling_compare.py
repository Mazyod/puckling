"""Benchmark upstream Facebook/Rasa Duckling (Haskell) via Docker HTTP.

Runs the same corpus that puckling's bench uses against `rasa/duckling`
on `localhost:18000/parse`, with matching locale/region/dim configuration:

    locale=en_US or ar_SA  (Duckling style)  ↔  Locale(EN/AR, KW)
    tz=Asia/Kuwait
    dims=["amount-of-money","duration","email","ordinal",
          "phone-number","time","url"]   (kebab-case in Duckling)

Output mirrors `bench run` shape for direct comparison. Wall time
includes HTTP localhost round-trip (TCP + JSON encode/decode), so the
numbers are NOT apples-to-apples vs puckling's in-process measurement —
Duckling has the HTTP overhead, puckling doesn't. We also measure the
HTTP baseline (a known-empty parse) to estimate the floor.

Caveat: the rasa/duckling image is `linux/amd64` running under Rosetta
on macOS arm64, which typically costs 20-30% perf. Flagged in output.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
import urllib.parse
from urllib.error import URLError
from urllib.request import Request, urlopen

from bench.corpus import CORPUS, length_bucket

DUCKLING_URL = "http://localhost:18000/parse"

# Duckling uses kebab-case dim names. Match prod's 7-dim filter.
DUCKLING_DIMS = '["amount-of-money","duration","email","ordinal","phone-number","time","url"]'

# Map puckling Lang+Region(KW) → Duckling locale code.
LOCALE_MAP = {"EN": "en_US", "AR": "ar_SA"}
TZ = "Asia/Kuwait"


def _post_parse(text: str, locale: str) -> bytes:
    body = urllib.parse.urlencode(
        {
            "text": text,
            "locale": locale,
            "tz": TZ,
            "dims": DUCKLING_DIMS,
        }
    ).encode("utf-8")
    req = Request(DUCKLING_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urlopen(req, timeout=10) as resp:
        return resp.read()


def _percentile(sorted_xs: list[float], p: float) -> float:
    if not sorted_xs:
        return 0.0
    rank = (p / 100.0) * (len(sorted_xs) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_xs) - 1)
    frac = rank - lo
    return sorted_xs[lo] * (1 - frac) + sorted_xs[hi] * frac


def _check_health() -> None:
    try:
        _post_parse("hello", "en_US")
    except URLError as e:
        print(f"ERROR: Duckling not reachable at {DUCKLING_URL}: {e}", file=sys.stderr)
        sys.exit(2)


def _measure_sample(text: str, locale: str, *, warmup: int, rounds: int) -> list[float]:
    for _ in range(warmup):
        _post_parse(text, locale)

    samples_us: list[float] = []
    for _ in range(rounds):
        t0 = time.perf_counter_ns()
        _post_parse(text, locale)
        samples_us.append((time.perf_counter_ns() - t0) / 1000.0)
    return samples_us


def _fmt_us(us: float) -> str:
    if us >= 1000:
        return f"{us/1000:7.2f}ms"
    return f"{us:7.1f}µs"


def _truncate(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--rounds", type=int, default=100)
    args = parser.parse_args()

    print("Duckling (Haskell, rasa/duckling Docker image, amd64-via-Rosetta)")
    print(f"  endpoint: {DUCKLING_URL}")
    print(f"  warmup={args.warmup}  rounds={args.rounds}")
    print()
    _check_health()

    # HTTP floor: an empty/minimal request to measure round-trip overhead.
    floor_samples = _measure_sample("a", "en_US", warmup=args.warmup, rounds=args.rounds)
    floor_samples.sort()
    floor_mean = statistics.fmean(floor_samples)
    print(f"HTTP+parse floor (text='a', en_US):  mean {_fmt_us(floor_mean)}  p50 {_fmt_us(_percentile(floor_samples, 50))}")
    print()

    cols = ("tag", "text", "mean", "p50", "p95", "p99", "stddev")
    widths = (22, 32, 9, 9, 9, 9, 9)
    header = "  ".join(f"{c:<{w}}" for c, w in zip(cols, widths, strict=True))
    print(header)
    print("-" * len(header))

    rows = []
    by_lang: dict[str, list[float]] = {"EN": [], "AR": []}
    by_bucket: dict[str, list[float]] = {"short": [], "medium": [], "long": []}

    for sample in CORPUS:
        locale = LOCALE_MAP[sample.lang.value]
        samples_us = _measure_sample(
            sample.text, locale, warmup=args.warmup, rounds=args.rounds
        )
        samples_us.sort()
        mean = statistics.fmean(samples_us)
        rows.append((sample.tag, sample.text, mean, samples_us))
        by_lang[sample.lang.value].extend(samples_us)
        by_bucket[length_bucket(sample)].extend(samples_us)

        print(
            "  ".join(
                [
                    f"{sample.tag:<22}",
                    f"{_truncate(sample.text, 32):<32}",
                    f"{_fmt_us(mean):<9}",
                    f"{_fmt_us(_percentile(samples_us, 50)):<9}",
                    f"{_fmt_us(_percentile(samples_us, 95)):<9}",
                    f"{_fmt_us(_percentile(samples_us, 99)):<9}",
                    f"{_fmt_us(statistics.pstdev(samples_us)):<9}",
                ]
            )
        )

    print()
    print("By locale (mean wall over all calls):")
    for lang, values in sorted(by_lang.items()):
        if values:
            print(f"  {lang}: {_fmt_us(statistics.fmean(values))}  (n={len(values)})")

    print("\nBy length bucket (mean wall over all calls):")
    for bucket in ("short", "medium", "long"):
        values = by_bucket[bucket]
        if values:
            print(f"  {bucket:>6}: {_fmt_us(statistics.fmean(values))}  (n={len(values)})")

    print("\nNote: numbers include HTTP localhost round-trip + JSON marshal.")
    print("      The HTTP+parse floor above is the irreducible per-call overhead.")
    print("      rasa/duckling Docker image is amd64-via-Rosetta on arm64 macOS;")
    print("      a native build would be ~20-30% faster.")


if __name__ == "__main__":
    main()
