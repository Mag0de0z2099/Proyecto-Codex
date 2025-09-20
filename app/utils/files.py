from __future__ import annotations

import hashlib
import mimetypes
import os
from typing import Tuple


def sha256_of_file(path: str, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def guess_mime(path: str) -> str | None:
    mime, _ = mimetypes.guess_type(path)
    return mime


def split_root_rel(full_path: str, root: str) -> Tuple[str, str]:
    """Devuelve ``(dir_rel, filename)`` relativo al directorio raíz ``root``."""

    relative = os.path.relpath(full_path, root)
    directory = os.path.dirname(relative)
    return ("" if directory == "." else directory, os.path.basename(relative))
