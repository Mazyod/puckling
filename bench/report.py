"""Report writers.

JSON schema is versioned so future runs that compare across schema bumps
fail loudly rather than silently.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from bench.harness import PROD_DIMS, PROD_REGION, PROD_TIMEOUT_MS, RunResult

SCHEMA_VERSION = 1


def _git_sha() -> tuple[str, bool]:
    """Return (sha, dirty). On any failure, returns ("unknown", False)."""
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], stderr=subprocess.DEVNULL, text=True
            ).strip()
        )
        return sha, dirty
    except Exception:
        return "unknown", False


def to_dict(result: RunResult) -> dict:
    sha, dirty = _git_sha()
    return {
        "schema_version": SCHEMA_VERSION,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "git_sha": sha,
        "git_dirty": dirty,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "config": {
            "warmup": result.warmup,
            "rounds": result.rounds,
            "dims": list(result.dims) if result.dims is not None else None,
            "prod_dims": list(PROD_DIMS),
            "region": PROD_REGION.value,
            "timeout_ms": PROD_TIMEOUT_MS,
        },
        "cells": [
            {
                "tag": c.sample.tag,
                "text": c.sample.text,
                "lang": c.sample.lang.value,
                "bucket": c.bucket,
                **asdict(c.agg),
            }
            for c in result.cells
        ],
    }


def write_json(result: RunResult, results_dir: Path) -> Path:
    results_dir.mkdir(parents=True, exist_ok=True)
    sha, dirty = _git_sha()
    short_sha = sha[:8] if sha != "unknown" else "nogit"
    if dirty:
        short_sha += "-dirty"
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = results_dir / f"{ts}-{short_sha}.json"
    path.write_text(json.dumps(to_dict(result), indent=2, ensure_ascii=False))
    return path
