from __future__ import annotations

import os
from typing import Any, Dict, Optional

from app.extensions import db


def _get_model():
    ArchivoAdjunto = None
    try:
        from app.models.parte_diaria import ArchivoAdjunto as _Adj  # type: ignore

        ArchivoAdjunto = _Adj
    except Exception:
        try:
            from app.models import ArchivoAdjunto as _Adj2  # type: ignore

            ArchivoAdjunto = _Adj2
        except Exception:
            return None
    return ArchivoAdjunto


def _build_query(model, *, parte_id: Optional[int] = None, run_id: Optional[int] = None):
    query = db.session.query(model)
    if parte_id:
        if hasattr(model, "parte_id"):
            query = query.filter(model.parte_id == parte_id)
        elif hasattr(model, "tabla") and hasattr(model, "registro_id"):
            query = query.filter(model.tabla == "partes_diarias", model.registro_id == parte_id)
    if run_id:
        if hasattr(model, "run_id"):
            query = query.filter(model.run_id == run_id)
        elif hasattr(model, "tabla") and hasattr(model, "registro_id"):
            query = query.filter(model.tabla == "checklist_runs", model.registro_id == run_id)
    return query


def _attachment_path(record) -> Optional[str]:
    for attr in ("ruta", "path", "filepath"):
        value = getattr(record, attr, None)
        if value:
            return value
    return None


def _attachment_name(record) -> str:
    for attr in ("nombre", "filename", "name", "titulo"):
        value = getattr(record, attr, None)
        if value:
            return value
    path = _attachment_path(record)
    if path:
        return os.path.basename(path)
    return f"archivo-{getattr(record, 'id', 'sin-id')}"


def _attachment_size(record) -> int:
    size = getattr(record, "size", None)
    if isinstance(size, int) and size >= 0:
        return size
    path = _attachment_path(record)
    if path and os.path.exists(path):
        try:
            return os.path.getsize(path)
        except OSError:
            return 0
    return 0


def count_evidencias(parte_id: Optional[int] = None, run_id: Optional[int] = None) -> int:
    """Retorna el número de evidencias asociadas a una parte o run."""

    ArchivoAdjunto = _get_model()
    if not ArchivoAdjunto:
        return 0

    try:
        query = _build_query(ArchivoAdjunto, parte_id=parte_id, run_id=run_id)
        return int(query.count() or 0)
    except Exception:
        return 0


def human_size(n: int) -> str:
    try:
        value = int(n or 0)
    except Exception:
        value = 0

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    idx = 0

    while size >= 1024 and idx < len(units) - 1:
        size /= 1024
        idx += 1

    if size.is_integer():
        size_str = f"{int(size)}"
    else:
        size_str = f"{size:.1f}"

    return f"{size_str} {units[idx]}"


def evidencias_summary(parte_id: Optional[int] = None, run_id: Optional[int] = None) -> Dict[str, Any]:
    """Resumen de evidencias por tipo y tamaño total."""

    ArchivoAdjunto = _get_model()
    if not ArchivoAdjunto:
        return {"total": 0, "by_ext": {"pdf": 0, "img": 0}, "bytes": 0, "size_h": "0 B"}

    try:
        query = _build_query(ArchivoAdjunto, parte_id=parte_id, run_id=run_id)
        records = query.all()
    except Exception:
        records = []

    total = len(records)
    bytes_sum = 0
    pdf = 0
    img = 0

    for record in records:
        bytes_sum += _attachment_size(record)
        name = _attachment_name(record).lower()
        ext = os.path.splitext(name)[1]
        if not ext:
            path = _attachment_path(record) or ""
            ext = os.path.splitext(path.lower())[1]
        if ext == ".pdf":
            pdf += 1
        elif ext in {".jpg", ".jpeg", ".png"}:
            img += 1

    return {
        "total": int(total or 0),
        "by_ext": {"pdf": int(pdf or 0), "img": int(img or 0)},
        "bytes": int(bytes_sum or 0),
        "size_h": human_size(bytes_sum or 0),
    }
