"""Compare two run JSONs and surface regressions/improvements.

`load_run` reads a JSON written by `report.write_json`.
`diff_runs` returns a per-cell delta keyed by tag+text (so a stable corpus
matches across runs even when ordering changes).
`gate` checks every cell's mean wall against a baseline + tolerance.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# Numeric fields we surface in the comparison table. Keep aligned with the
# schema written by `report.to_dict`.
_METRIC_FIELDS = (
    "wall_mean_us",
    "wall_p50_us",
    "wall_p95_us",
    "wall_p99_us",
    "cold_wall_us",
)


@dataclass(frozen=True, slots=True)
class CellDelta:
    tag: str
    text: str
    a: dict
    b: dict

    def pct(self, field: str) -> float | None:
        av, bv = self.a.get(field), self.b.get(field)
        if not av or not bv:
            return None
        return (bv - av) / av * 100.0


def load_run(path: Path) -> dict:
    return json.loads(path.read_text())


def _key(cell: dict) -> tuple[str, str]:
    return (cell["tag"], cell["text"])


def diff_runs(a: dict, b: dict) -> tuple[list[CellDelta], list[tuple[str, str]], list[tuple[str, str]]]:
    """Return (matched deltas, only_in_a, only_in_b)."""
    a_by_key = {_key(c): c for c in a["cells"]}
    b_by_key = {_key(c): c for c in b["cells"]}
    deltas = [
        CellDelta(tag=tag, text=text, a=a_by_key[(tag, text)], b=b_by_key[(tag, text)])
        for (tag, text) in a_by_key.keys() & b_by_key.keys()
    ]
    only_a = sorted(a_by_key.keys() - b_by_key.keys())
    only_b = sorted(b_by_key.keys() - a_by_key.keys())
    return deltas, only_a, only_b


def gate(
    *,
    baseline: dict,
    candidate: dict,
    tolerance_pct: float,
    field: str = "wall_mean_us",
) -> list[CellDelta]:
    """Cells in `candidate` that regressed vs `baseline` beyond `tolerance_pct`."""
    deltas, _, _ = diff_runs(baseline, candidate)
    return [d for d in deltas if (p := d.pct(field)) is not None and p > tolerance_pct]


def _fmt_us(us: float) -> str:
    if us >= 1000:
        return f"{us/1000:7.2f}ms"
    return f"{us:7.1f}µs"


def _fmt_pct(p: float | None) -> str:
    if p is None:
        return "    n/a"
    sign = "+" if p >= 0 else ""
    return f"{sign}{p:6.1f}%"


def print_diff(a: dict, b: dict) -> None:
    deltas, only_a, only_b = diff_runs(a, b)
    print(f"A: {a.get('git_sha', '?')[:8]} {a.get('timestamp', '?')}  rounds={a['config']['rounds']}")
    print(f"B: {b.get('git_sha', '?')[:8]} {b.get('timestamp', '?')}  rounds={b['config']['rounds']}")
    print()

    cols = ("tag", "text", "A mean", "B mean", "Δ mean", "Δ p95", "Δ p99")
    widths = (22, 32, 9, 9, 8, 8, 8)
    header = "  ".join(f"{c:<{w}}" for c, w in zip(cols, widths, strict=True))
    print(header)
    print("-" * len(header))

    deltas.sort(key=lambda d: -(d.pct("wall_mean_us") or 0))
    for d in deltas:
        text = d.text if len(d.text) <= widths[1] else d.text[: widths[1] - 1] + "…"
        row = (
            d.tag,
            text,
            _fmt_us(d.a["wall_mean_us"]),
            _fmt_us(d.b["wall_mean_us"]),
            _fmt_pct(d.pct("wall_mean_us")),
            _fmt_pct(d.pct("wall_p95_us")),
            _fmt_pct(d.pct("wall_p99_us")),
        )
        print("  ".join(f"{v:<{w}}" for v, w in zip(row, widths, strict=True)))

    if only_a:
        print(f"\nOnly in A ({len(only_a)}):")
        for tag, text in only_a:
            print(f"  {tag}  {text!r}")
    if only_b:
        print(f"\nOnly in B ({len(only_b)}):")
        for tag, text in only_b:
            print(f"  {tag}  {text!r}")
