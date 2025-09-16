from __future__ import annotations
from pathlib import Path
from flask import Flask


def ensure_dirs(app: Flask) -> None:
    data_dir = Path(app.config["DATA_DIR"])
    base = Path(app.instance_path)

    paths = {
        base,
        base / ".tmp",
        base / "uploads",
        base / "exports",
        base / "logs",
        data_dir,
        data_dir / "uploads",
        data_dir / "logs",
    }

    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
