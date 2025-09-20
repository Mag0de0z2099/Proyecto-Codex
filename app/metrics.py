"""Prometheus metrics used across the Codex application."""

from __future__ import annotations

import os
from pathlib import Path

_prom_dir = os.getenv("PROMETHEUS_MULTIPROC_DIR")
if not _prom_dir:
    default_dir = Path(os.getenv("PROMETHEUS_MULTIPROC_DIR_DEFAULT", "/tmp/codex-prom"))
    default_dir.mkdir(parents=True, exist_ok=True)
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = str(default_dir)
    _prom_dir = str(default_dir)
else:
    Path(_prom_dir).mkdir(parents=True, exist_ok=True)

from prometheus_client import Counter, Gauge, Histogram

scan_created_total = Counter(
    "scan_created_total",
    "Total number of assets created while scanning folders.",
)
scan_updated_total = Counter(
    "scan_updated_total",
    "Total number of assets updated while scanning folders.",
)
scan_skipped_total = Counter(
    "scan_skipped_total",
    "Total number of assets that did not require changes during scans.",
)
scan_runs_total = Counter(
    "scan_runs_total",
    "Total number of folder scan executions.",
)
scan_duration_seconds = Histogram(
    "scan_duration_seconds",
    "Time spent scanning individual folders.",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, float("inf")),
)
scan_lock = Gauge(
    "scan_lock",
    "Whether the scanner lock is currently held (1=yes, 0=no).",
    multiprocess_mode="livesum",
)
folders_registered = Gauge(
    "folders_registered",
    "Current number of folders registered in the database.",
    multiprocess_mode="livesum",
)
assets_registered = Gauge(
    "assets_registered",
    "Current number of assets registered in the database.",
    multiprocess_mode="livesum",
)


def cleanup_multiprocess_directory() -> None:
    """Remove leftover metric shard files when using multiprocess mode."""

    prom_path = Path(_prom_dir or "")
    if not prom_path.exists():  # pragma: no cover - defensive guard
        return

    for child in prom_path.iterdir():
        if not child.is_file():
            continue
        try:
            child.unlink()
        except FileNotFoundError:  # pragma: no cover - benign race condition
            continue


__all__ = [
    "scan_created_total",
    "scan_updated_total",
    "scan_skipped_total",
    "scan_runs_total",
    "scan_duration_seconds",
    "scan_lock",
    "folders_registered",
    "assets_registered",
    "cleanup_multiprocess_directory",
]
