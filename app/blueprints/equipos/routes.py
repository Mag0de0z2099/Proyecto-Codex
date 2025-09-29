from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.db import db
from app.models import Equipo
from app.utils.pagination import paginate

from . import bp


@bp.get("/")
@login_required
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


@bp.get("/nuevo")
@login_required
def nuevo():
    return render_template("equipos/form.html", equipo=None)


@bp.post("/crear")
@login_required
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
            return redirect(url_for("equipos.nuevo"))
    if not data.get("codigo") or not data.get("tipo"):
        flash("Código y tipo son obligatorios", "error")
        return redirect(url_for("equipos.nuevo"))
    equipo = Equipo(**data)
    db.session.add(equipo)
    db.session.commit()
    flash("Equipo creado", "success")
    return redirect(url_for("equipos.index"))


@bp.get("/<int:equipo_id>/editar")
@login_required
def editar(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)
    return render_template("equipos/form.html", equipo=equipo)


@bp.post("/<int:equipo_id>/actualizar")
@login_required
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
                return redirect(url_for("equipos.editar", equipo_id=equipo.id))
        setattr(equipo, key, value)
    db.session.commit()
    flash("Equipo actualizado", "success")
    return redirect(url_for("equipos.index"))


@bp.post("/<int:equipo_id>/eliminar")
@login_required
def eliminar(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)
    db.session.delete(equipo)
    db.session.commit()
    flash("Equipo eliminado", "success")
    return redirect(url_for("equipos.index"))


@bp.get("/<int:equipo_id>")
@login_required
def detalle(equipo_id: int):
    equipo = Equipo.query.get_or_404(equipo_id)
    return render_template("equipos/detalle.html", equipo=equipo)
