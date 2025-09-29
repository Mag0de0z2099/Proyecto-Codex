import os
import csv
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from werkzeug.utils import secure_filename
from app.extensions import db

try:
    from app.models.equipo import Equipo
except Exception:  # pragma: no cover - fallback cuando el módulo cambia
    from app.models import Equipo

try:
    from app.models.operador import Operador
except Exception:  # pragma: no cover - fallback cuando el módulo cambia
    from app.models import Operador

from app.models.parte_diaria import ParteDiaria, ArchivoAdjunto

bp = Blueprint("partes", __name__, url_prefix="/partes", template_folder="../../templates/partes")


@bp.before_request
def _guard():
    if current_app.config.get("SECURITY_DISABLED") or current_app.config.get("LOGIN_DISABLED"):
        return None


def _parse_date(value, default=None):
    if not value:
        return default
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return default


def _save_upload(file_storage, subdir="partes"):
    if not file_storage or not file_storage.filename:
        return None
    root = current_app.config.get("UPLOAD_DIR", "/opt/render/project/data/uploads")
    os.makedirs(os.path.join(root, subdir), exist_ok=True)
    fname = secure_filename(file_storage.filename)
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    final_name = f"{ts}_{fname}"
    abs_path = os.path.join(root, subdir, final_name)
    file_storage.save(abs_path)
    return abs_path, final_name


@bp.get("/")
def index():
    desde = _parse_date(request.args.get("desde"))
    hasta = _parse_date(request.args.get("hasta"))
    equipo_id = request.args.get("equipo_id", type=int)

    query = ParteDiaria.query
    if desde:
        query = query.filter(ParteDiaria.fecha >= desde)
    if hasta:
        query = query.filter(ParteDiaria.fecha <= hasta)
    if equipo_id:
        query = query.filter(ParteDiaria.equipo_id == equipo_id)

    page = request.args.get("page", 1, type=int)
    per_page = 10
    pagination = query.order_by(ParteDiaria.fecha.desc(), ParteDiaria.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    equipos = Equipo.query.order_by(Equipo.id.desc()).all() if hasattr(Equipo, "query") else []
    return render_template(
        "partes/index.html",
        pagination=pagination,
        rows=pagination.items,
        equipos=equipos,
        desde=desde,
        hasta=hasta,
        equipo_id=equipo_id,
    )


@bp.route("/new", methods=["GET", "POST"])
def create():
    equipos = Equipo.query.order_by(Equipo.id.desc()).all() if hasattr(Equipo, "query") else []
    operadores = Operador.query.order_by(Operador.id.desc()).all() if hasattr(Operador, "query") else []

    if request.method == "POST":
        parte = ParteDiaria(
            fecha=_parse_date(request.form.get("fecha"), default=date.today()),
            equipo_id=request.form.get("equipo_id", type=int),
            operador_id=request.form.get("operador_id", type=int),
            horas_trabajo=request.form.get("horas_trabajo", type=float) or 0,
            actividad=(request.form.get("actividad") or "").strip(),
            incidencias=(request.form.get("incidencias") or "").strip(),
            notas=(request.form.get("notas") or "").strip(),
        )
        db.session.add(parte)
        db.session.commit()

        for storage in request.files.getlist("adjuntos"):
            saved = _save_upload(storage, subdir="partes")
            if saved:
                abs_path, fname = saved
                db.session.add(
                    ArchivoAdjunto(
                        tabla="partes_diarias",
                        registro_id=parte.id,
                        filename=fname,
                        path=abs_path,
                    )
                )
        db.session.commit()

        flash("Parte diaria creada", "success")
        return redirect(url_for("partes.index"))

    return render_template("partes/form.html", item=None, equipos=equipos, operadores=operadores)


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    parte = ParteDiaria.query.get_or_404(id)
    equipos = Equipo.query.order_by(Equipo.id.desc()).all() if hasattr(Equipo, "query") else []
    operadores = Operador.query.order_by(Operador.id.desc()).all() if hasattr(Operador, "query") else []

    if request.method == "POST":
        parte.fecha = _parse_date(request.form.get("fecha"), default=parte.fecha)
        parte.equipo_id = request.form.get("equipo_id", type=int)
        parte.operador_id = request.form.get("operador_id", type=int)
        parte.horas_trabajo = request.form.get("horas_trabajo", type=float) or 0
        parte.actividad = (request.form.get("actividad") or "").strip()
        parte.incidencias = (request.form.get("incidencias") or "").strip()
        parte.notas = (request.form.get("notas") or "").strip()
        db.session.commit()

        for storage in request.files.getlist("adjuntos"):
            saved = _save_upload(storage, subdir="partes")
            if saved:
                abs_path, fname = saved
                db.session.add(
                    ArchivoAdjunto(
                        tabla="partes_diarias",
                        registro_id=parte.id,
                        filename=fname,
                        path=abs_path,
                    )
                )
        db.session.commit()

        flash("Parte diaria actualizada", "success")
        return redirect(url_for("partes.index"))

    adjuntos = ArchivoAdjunto.query.filter_by(tabla="partes_diarias", registro_id=parte.id).all()
    return render_template(
        "partes/form.html",
        item=parte,
        equipos=equipos,
        operadores=operadores,
        adjuntos=adjuntos,
    )


@bp.post("/<int:id>/delete")
def delete(id):
    parte = ParteDiaria.query.get_or_404(id)
    attachments = ArchivoAdjunto.query.filter_by(tabla="partes_diarias", registro_id=parte.id).all()
    for attachment in attachments:
        try:
            if os.path.exists(attachment.path):
                os.remove(attachment.path)
        except Exception:
            pass
    ArchivoAdjunto.query.filter_by(tabla="partes_diarias", registro_id=parte.id).delete()
    db.session.delete(parte)
    db.session.commit()
    flash("Parte diaria eliminada", "success")
    return redirect(url_for("partes.index"))


@bp.get("/export")
def export_csv():
    desde = _parse_date(request.args.get("desde"))
    hasta = _parse_date(request.args.get("hasta"))
    equipo_id = request.args.get("equipo_id", type=int)

    query = ParteDiaria.query
    if desde:
        query = query.filter(ParteDiaria.fecha >= desde)
    if hasta:
        query = query.filter(ParteDiaria.fecha <= hasta)
    if equipo_id:
        query = query.filter(ParteDiaria.equipo_id == equipo_id)

    rows = query.order_by(ParteDiaria.fecha.desc(), ParteDiaria.id.desc()).all()

    root = current_app.config.get("UPLOAD_DIR", "/opt/render/project/data/uploads")
    os.makedirs(root, exist_ok=True)
    out_path = os.path.join(root, "export_partes.csv")

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "id",
            "fecha",
            "equipo_id",
            "operador_id",
            "horas_trabajo",
            "actividad",
            "incidencias",
            "notas",
        ])
        for row in rows:
            writer.writerow(
                [
                    row.id,
                    row.fecha.isoformat() if row.fecha else "",
                    row.equipo_id,
                    row.operador_id,
                    row.horas_trabajo,
                    row.actividad or "",
                    row.incidencias or "",
                    row.notas or "",
                ]
            )

    return send_file(out_path, as_attachment=True, download_name="partes_diarias.csv")
