from __future__ import annotations

import mimetypes
import os
import uuid
from types import SimpleNamespace
from typing import Iterable

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from app.security.authz import require_login
from werkzeug.utils import secure_filename

from app.extensions import db

bp = Blueprint(
    "archivos_bp",
    __name__,
    url_prefix="/archivos",
    template_folder="../../templates/archivos",
)

ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB


def _imports():
    try:
        from app.models.parte_diaria import ParteDiaria, ArchivoAdjunto  # type: ignore
    except Exception:
        ParteDiaria = None
        try:
            from app.models import ArchivoAdjunto  # type: ignore
        except Exception:
            ArchivoAdjunto = None
    try:
        from app.models.checklist import ChecklistRun  # type: ignore
    except Exception:
        try:
            from app.models import ChecklistRun  # type: ignore
        except Exception:
            ChecklistRun = None
    return ParteDiaria, ChecklistRun, ArchivoAdjunto


def _upload_dir() -> str:
    dest = current_app.config.get("UPLOAD_DIR") or "/opt/render/project/data/uploads"
    os.makedirs(dest, exist_ok=True)
    return dest


def _attachment_path(record) -> str | None:
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
    return os.path.basename(path) if path else f"archivo-{getattr(record, 'id', 'sin-id')}"


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


def _label_for(record) -> str:
    labels: list[str] = []
    if hasattr(record, "parte_id") and getattr(record, "parte_id", None):
        labels.append(f"Parte #{getattr(record, 'parte_id')}")
    if hasattr(record, "run_id") and getattr(record, "run_id", None):
        labels.append(f"ChecklistRun #{getattr(record, 'run_id')}")
    tabla = getattr(record, "tabla", "")
    registro_id = getattr(record, "registro_id", None)
    if tabla == "partes_diarias" and registro_id:
        labels.append(f"Parte #{registro_id}")
    if tabla == "checklist_runs" and registro_id:
        labels.append(f"ChecklistRun #{registro_id}")
    return " · ".join(labels) if labels else "—"


def _build_payload(model, *, name: str, path: str, mime: str, size: int, parte_id: int | None, run_id: int | None):
    payload = {}
    if hasattr(model, "nombre"):
        payload["nombre"] = name
    elif hasattr(model, "filename"):
        payload["filename"] = name
    elif hasattr(model, "name"):
        payload["name"] = name

    if hasattr(model, "ruta"):
        payload["ruta"] = path
    elif hasattr(model, "path"):
        payload["path"] = path
    elif hasattr(model, "filepath"):
        payload["filepath"] = path

    if hasattr(model, "mimetype"):
        payload["mimetype"] = mime
    if hasattr(model, "size"):
        payload["size"] = size

    if parte_id:
        if hasattr(model, "parte_id"):
            payload.setdefault("parte_id", parte_id)
        if hasattr(model, "registro_id") and hasattr(model, "tabla"):
            payload.setdefault("tabla", "partes_diarias")
            payload.setdefault("registro_id", parte_id)
    if run_id:
        if hasattr(model, "run_id"):
            payload.setdefault("run_id", run_id)
        if hasattr(model, "registro_id") and hasattr(model, "tabla"):
            payload.setdefault("tabla", "checklist_runs")
            payload.setdefault("registro_id", run_id)

    if hasattr(model, "tabla"):
        payload.setdefault("tabla", "otros")
    if hasattr(model, "registro_id"):
        payload.setdefault("registro_id", parte_id or run_id or 0)

    return payload


def _query_filtered(model, *, parte_id: int | None, run_id: int | None):
    query = db.session.query(model)
    if parte_id:
        if hasattr(model, "parte_id"):
            query = query.filter_by(parte_id=parte_id)
        elif hasattr(model, "tabla") and hasattr(model, "registro_id"):
            query = query.filter_by(tabla="partes_diarias", registro_id=parte_id)
    if run_id:
        if hasattr(model, "run_id"):
            query = query.filter_by(run_id=run_id)
        elif hasattr(model, "tabla") and hasattr(model, "registro_id"):
            query = query.filter_by(tabla="checklist_runs", registro_id=run_id)
    return query


def _serialize_records(records: Iterable) -> list[SimpleNamespace]:
    items: list[SimpleNamespace] = []
    for record in records:
        size_bytes = _attachment_size(record)
        items.append(
            SimpleNamespace(
                id=getattr(record, "id", None),
                name=_attachment_name(record),
                size_kb=size_bytes // 1024,
                label=_label_for(record),
                record=record,
            )
        )
    return items


def _redirect_with_filters(parte_id: int | None, run_id: int | None):
    params = {}
    if parte_id:
        params["parte_id"] = parte_id
    if run_id:
        params["run_id"] = run_id
    return redirect(url_for("archivos_bp.index", **params))


@bp.get("/")
@require_login
def index():
    parte_id = request.args.get("parte_id", type=int)
    run_id = request.args.get("run_id", type=int)
    ParteDiaria, ChecklistRun, ArchivoAdjunto = _imports()
    if not ArchivoAdjunto:
        flash("El modelo de archivos no está disponible.", "warning")
        archivos = []
    else:
        archivos_query = _query_filtered(ArchivoAdjunto, parte_id=parte_id, run_id=run_id)
        archivos = _serialize_records(archivos_query.order_by(ArchivoAdjunto.id.desc()).all())
    return render_template(
        "archivos/index.html",
        archivos=archivos,
        parte_id=parte_id,
        run_id=run_id,
    )


@bp.post("/upload")
@require_login
def upload():
    parte_id = request.form.get("parte_id", type=int)
    run_id = request.form.get("run_id", type=int)
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Selecciona un archivo", "error")
        return _redirect_with_filters(parte_id, run_id)

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        flash("Extensión no permitida", "error")
        return _redirect_with_filters(parte_id, run_id)

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_SIZE:
        flash("Archivo demasiado grande (máx 10MB)", "error")
        return _redirect_with_filters(parte_id, run_id)

    upload_root = _upload_dir()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    abs_path = os.path.join(upload_root, unique_name)
    file.save(abs_path)

    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    ParteDiaria, ChecklistRun, ArchivoAdjunto = _imports()
    if not ArchivoAdjunto:
        flash("El modelo de archivos no está disponible.", "error")
        try:
            os.remove(abs_path)
        except OSError:
            pass
        return _redirect_with_filters(parte_id, run_id)

    payload = _build_payload(
        ArchivoAdjunto,
        name=filename,
        path=abs_path,
        mime=mime,
        size=size,
        parte_id=parte_id,
        run_id=run_id,
    )
    adjunto = ArchivoAdjunto(**payload)
    db.session.add(adjunto)
    db.session.commit()
    flash("Archivo subido", "success")
    return _redirect_with_filters(parte_id, run_id)


@bp.get("/<int:attachment_id>/download")
@require_login
def download(attachment_id: int):
    _, _, ArchivoAdjunto = _imports()
    if not ArchivoAdjunto:
        abort(404)
    adjunto = db.session.get(ArchivoAdjunto, attachment_id)
    if not adjunto:
        abort(404)
    path = _attachment_path(adjunto)
    if not path or not os.path.exists(path):
        abort(404)
    name = _attachment_name(adjunto)
    mimetype = getattr(adjunto, "mimetype", None) or mimetypes.guess_type(name)[0]
    return send_file(path, as_attachment=True, download_name=name, mimetype=mimetype)


@bp.post("/<int:attachment_id>/delete")
@require_login
def delete(attachment_id: int):
    parte_id = request.form.get("parte_id", type=int)
    run_id = request.form.get("run_id", type=int)
    _, _, ArchivoAdjunto = _imports()
    if not ArchivoAdjunto:
        abort(404)
    adjunto = db.session.get(ArchivoAdjunto, attachment_id)
    if not adjunto:
        abort(404)
    path = _attachment_path(adjunto)
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            current_app.logger.warning("No se pudo eliminar archivo %s", path)
    db.session.delete(adjunto)
    db.session.commit()
    flash("Archivo eliminado", "success")
    return _redirect_with_filters(parte_id, run_id)
