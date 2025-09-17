from __future__ import annotations
from pathlib import Path
import os
from flask import Flask, current_app


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


def data_dir() -> Path:
    base = current_app.config.get("DATA_DIR") or os.getenv("DATA_DIR") or "./data"
    path = Path(base).resolve()
    path.mkdir(parents=True, exist_ok=True)
    folders_dir = path / "folders"
    folders_dir.mkdir(parents=True, exist_ok=True)
    return folders_dir


def folder_path(folder_id: int) -> Path:
    return data_dir() / str(folder_id)


def ensure_folder_dir(folder_id: int) -> Path:
    folder = folder_path(folder_id)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def remove_folder_dir_if_empty(folder_id: int) -> bool:
    folder = folder_path(folder_id)
    if not folder.exists():
        return True
    try:
        next(folder.iterdir())
        return False
    except StopIteration:
        folder.rmdir()
        return True
