from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for

from app.db import db
from app.models import Operador

from . import bp


@bp.get("/")
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
def nuevo():
    return render_template("operadores/form.html", op=None)


@bp.post("/crear")
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
def editar(op_id: int):
    op = Operador.query.get_or_404(op_id)
    return render_template("operadores/form.html", op=op)


@bp.post("/<int:op_id>/actualizar")
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
def eliminar(op_id: int):
    op = Operador.query.get_or_404(op_id)
    db.session.delete(op)
    db.session.commit()
    flash("Operador eliminado", "success")
    return redirect(url_for("operadores.index"))


@bp.get("/<int:op_id>")
def detalle(op_id: int):
    op = Operador.query.get_or_404(op_id)
    return render_template("operadores/detalle.html", op=op)
