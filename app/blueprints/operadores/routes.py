from __future__ import annotations

from datetime import datetime, date, timedelta
import csv
import os

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from sqlalchemy import or_

from app.extensions import db
from app.models.operador import Operador

from . import bp


@bp.before_request
def _guard():  # type: ignore[func-returns-value]
    if current_app.config.get("SECURITY_DISABLED") or current_app.config.get(
        "LOGIN_DISABLED"
    ):
        return None
    return None


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except Exception:
        return None


@bp.get("/")
def index():
    q = (request.args.get("q") or "").strip()
    vence_en = request.args.get("vence_en", type=int)
    page = request.args.get("page", 1, type=int)
    per_page = 10

    query = Operador.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Operador.nombre.ilike(like),
                Operador.doc_id.ilike(like),
                Operador.notas.ilike(like),
            )
        )
    if vence_en:
        limite = date.today() + timedelta(days=vence_en)
        query = query.filter(
            Operador.licencia_vence.isnot(None),
            Operador.licencia_vence <= limite,
        )

    pagination = query.order_by(Operador.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template(
        "operadores/index.html",
        pagination=pagination,
        rows=pagination.items,
        q=q,
        vence_en=vence_en,
    )


@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        operador = Operador(
            nombre=(request.form.get("nombre") or "").strip(),
            doc_id=(request.form.get("doc_id") or "").strip(),
            licencia_vence=_parse_date(request.form.get("licencia_vence")),
            notas=(request.form.get("notas") or "").strip(),
            estatus=(request.form.get("estatus") or "activo").strip(),
        )
        db.session.add(operador)
        db.session.commit()
        flash("Operador creado", "success")
        return redirect(url_for("operadores_bp.index"))
    return render_template("operadores/form.html", item=None)


@bp.route("/<int:operador_id>/edit", methods=["GET", "POST"])
def edit(operador_id: int):
    operador = Operador.query.get_or_404(operador_id)
    if request.method == "POST":
        for key in ("nombre", "doc_id", "notas", "estatus"):
            if key in request.form:
                setattr(operador, key, (request.form.get(key) or "").strip())
        operador.licencia_vence = _parse_date(request.form.get("licencia_vence"))
        db.session.commit()
        flash("Operador actualizado", "success")
        return redirect(url_for("operadores_bp.index"))
    return render_template("operadores/form.html", item=operador)


@bp.post("/<int:operador_id>/delete")
def delete(operador_id: int):
    operador = Operador.query.get_or_404(operador_id)
    db.session.delete(operador)
    db.session.commit()
    flash("Operador eliminado", "success")
    return redirect(url_for("operadores_bp.index"))


@bp.get("/export")
def export_csv():
    q = (request.args.get("q") or "").strip()
    vence_en = request.args.get("vence_en", type=int)

    query = Operador.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Operador.nombre.ilike(like),
                Operador.doc_id.ilike(like),
                Operador.notas.ilike(like),
            )
        )
    if vence_en:
        limite = date.today() + timedelta(days=vence_en)
        query = query.filter(
            Operador.licencia_vence.isnot(None),
            Operador.licencia_vence <= limite,
        )

    rows = query.order_by(Operador.id.desc()).all()
    output_dir = current_app.config.get(
        "UPLOAD_DIR", "/opt/render/project/data/uploads"
    )
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "operadores.csv")

    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "id",
                "nombre",
                "doc_id",
                "licencia_vence",
                "estatus",
                "notas",
                "dias_para_vencer",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.id,
                    row.nombre or "",
                    row.doc_id or "",
                    row.licencia_vence.isoformat() if row.licencia_vence else "",
                    row.estatus or "",
                    (row.notas or "").replace("\n", " ").strip(),
                    row.dias_para_vencer() if row.dias_para_vencer() is not None else "",
                ]
            )

    return send_file(output_path, as_attachment=True, download_name="operadores.csv")
