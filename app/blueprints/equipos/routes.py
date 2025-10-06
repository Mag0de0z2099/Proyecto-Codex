from __future__ import annotations

import csv
import os

from flask import current_app, flash, redirect, render_template, request, send_file, url_for

from app.security.authz import require_login

from app.db import db
from app.models import Equipo
from app.utils.pagination import paginate

from . import bp


@bp.get("/")
@require_login
def index():
    q = (request.args.get("q", "") or "").strip()
    query = Equipo.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Equipo.codigo.ilike(like),
                Equipo.tipo.ilike(like),
                Equipo.marca.ilike(like),
            )
        )
    query = query.order_by(Equipo.codigo.asc())
    page = request.args.get("page", type=int) or 1
    per_page = min(max(request.args.get("per_page", type=int) or 20, 1), 100)
    equipos, pagination = paginate(query, page=page, per_page=per_page)
    return render_template(
        "equipos/index.html",
        equipos=equipos,
        q=q,
        pagination=pagination,
    )


@bp.get("/export")
@require_login
def export_csv():
    rows = Equipo.query.order_by(Equipo.id.desc()).all()
    out_dir = current_app.config.get(
        "UPLOAD_DIR", "/opt/render/project/data/uploads"
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "equipos.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "nombre", "serie", "estatus", "descripcion"])
        for row in rows:
            writer.writerow(
                [
                    row.id,
                    getattr(row, "nombre", "") or "",
                    getattr(row, "serie", "") or "",
                    getattr(row, "status", "") or "",
                    getattr(row, "descripcion", "") or "",
                ]
            )
    return send_file(out_path, as_attachment=True, download_name="equipos.csv")


@bp.get("/nuevo")
@require_login
def nuevo():
    return render_template("equipos/form.html", equipo=None)


@bp.post("/crear")
@require_login
def crear():
    data = {
        k: request.form.get(k) for k in [
            "codigo",
            "tipo",
            "marca",
            "modelo",
            "serie",
            "placas",
            "status",
            "ubicacion",
        ]
    }
    horas_uso_raw = request.form.get("horas_uso")
    if horas_uso_raw:
        try:
            data["horas_uso"] = float(horas_uso_raw)
        except (TypeError, ValueError):
            flash("Horas de uso inválidas", "error")
            return redirect(url_for("equipos_bp.nuevo"))
    if not data.get("codigo") or not data.get("tipo"):
        flash("Código y tipo son obligatorios", "error")
        return redirect(url_for("equipos_bp.nuevo"))
    equipo = Equipo(**data)
    db.session.add(equipo)
    db.session.commit()
    flash("Equipo creado", "success")
    return redirect(url_for("equipos_bp.index"))


@bp.get("/<int:equipo_id>/editar")
@require_login
def editar(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)
    return render_template("equipos/form.html", equipo=equipo)


@bp.post("/<int:equipo_id>/actualizar")
@require_login
def actualizar(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)
    for key in [
        "codigo",
        "tipo",
        "marca",
        "modelo",
        "serie",
        "placas",
        "status",
        "ubicacion",
        "horas_uso",
    ]:
        value = request.form.get(key)
        if value is None or value == "":
            continue
        if key == "horas_uso":
            try:
                value = float(value)
            except (TypeError, ValueError):
                flash("Horas de uso inválidas", "error")
                return redirect(url_for("equipos_bp.editar", equipo_id=equipo.id))
        setattr(equipo, key, value)
    db.session.commit()
    flash("Equipo actualizado", "success")
    return redirect(url_for("equipos_bp.index"))


@bp.post("/<int:equipo_id>/eliminar")
@require_login
def eliminar(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)
    db.session.delete(equipo)
    db.session.commit()
    flash("Equipo eliminado", "success")
    return redirect(url_for("equipos_bp.index"))


@bp.get("/<int:equipo_id>")
@require_login
def detalle(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)
    return render_template("equipos/detalle.html", equipo=equipo)
