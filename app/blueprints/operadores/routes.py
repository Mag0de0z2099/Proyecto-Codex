from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.db import db
from app.models import Operador

from . import bp


@bp.get("/")
@login_required
def index():
    q = (request.args.get("q", "") or "").strip()
    query = Operador.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Operador.nombre.ilike(like),
                Operador.identificacion.ilike(like),
                Operador.puesto.ilike(like),
            )
        )
    operadores = query.order_by(Operador.nombre.asc()).all()
    return render_template("operadores/index.html", operadores=operadores, q=q)


@bp.get("/nuevo")
@login_required
def nuevo():
    return render_template("operadores/form.html", op=None)


@bp.post("/crear")
@login_required
def crear():
    data = {
        k: request.form.get(k)
        for k in ["nombre", "identificacion", "licencia", "puesto", "telefono", "status"]
    }
    if not (data.get("nombre") or "").strip():
        flash("El nombre es obligatorio", "error")
        return redirect(url_for("operadores.nuevo"))
    operador = Operador(**data)
    db.session.add(operador)
    db.session.commit()
    flash("Operador creado", "success")
    return redirect(url_for("operadores.index"))


@bp.get("/<int:op_id>/editar")
@login_required
def editar(op_id: int):
    op = Operador.query.get_or_404(op_id)
    return render_template("operadores/form.html", op=op)


@bp.post("/<int:op_id>/actualizar")
@login_required
def actualizar(op_id: int):
    op = Operador.query.get_or_404(op_id)
    for key in ["nombre", "identificacion", "licencia", "puesto", "telefono", "status"]:
        value = request.form.get(key)
        if value is None or value == "":
            continue
        setattr(op, key, value)
    db.session.commit()
    flash("Operador actualizado", "success")
    return redirect(url_for("operadores.index"))


@bp.post("/<int:op_id>/eliminar")
@login_required
def eliminar(op_id: int):
    op = Operador.query.get_or_404(op_id)
    db.session.delete(op)
    db.session.commit()
    flash("Operador eliminado", "success")
    return redirect(url_for("operadores.index"))


@bp.get("/<int:op_id>")
@login_required
def detalle(op_id: int):
    op = Operador.query.get_or_404(op_id)
    return render_template("operadores/detalle.html", op=op)
