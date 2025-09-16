from __future__ import annotations
from pathlib import Path
from flask import Flask

def ensure_dirs(app: Flask) -> None:
    data_dir: Path = app.config["DATA_DIR"]
    uploads = data_dir / "uploads"
    logs = data_dir / "logs"
    for p in (data_dir, uploads, logs):
        p.mkdir(parents=True, exist_ok=True)
