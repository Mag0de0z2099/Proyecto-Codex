from __future__ import annotations

from typing import Optional

from sqlalchemy import func

from app.extensions import db


def count_evidencias(parte_id: Optional[int] = None, run_id: Optional[int] = None) -> int:
    """
    Retorna el número de archivos adjuntos vinculados a una ParteDiaria o ChecklistRun.
    Importa modelos de forma tolerante a estructura de proyecto.
    """

    ArchivoAdjunto = None
    try:
        from app.models.parte_diaria import ArchivoAdjunto as _Adj

        ArchivoAdjunto = _Adj
    except Exception:
        try:
            from app.models.archivo import ArchivoAdjunto as _Adj2

            ArchivoAdjunto = _Adj2
        except Exception:
            return 0  # si no existe el modelo, devolvemos 0

    q = db.session.query(func.count(ArchivoAdjunto.id))
    if parte_id:
        q = q.filter(ArchivoAdjunto.parte_id == parte_id)
    if run_id:
        q = q.filter(ArchivoAdjunto.run_id == run_id)
    try:
        return int(q.scalar() or 0)
    except Exception:
        return 0
