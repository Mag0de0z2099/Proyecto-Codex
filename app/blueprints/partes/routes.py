from __future__ import annotations

import csv
import io
from datetime import date

from flask import flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.db import db
from app.models import ActividadDiaria, Equipo, ParteDiaria
from app.utils.pagination import paginate

try:
    from app.models import Operador
except Exception:  # pragma: no cover - apps sin operadores
    Operador = None

from . import bp


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        flash("Fecha inválida, se ignoró el filtro.", "warning")
        return None


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        flash("Valor numérico inválido, se ignoró.", "warning")
        return None


@bp.get("/")
@login_required
def index():
    d1_raw = request.args.get("d1")
    d2_raw = request.args.get("d2")
    q = (request.args.get("q") or "").strip()

    d1 = _parse_date(d1_raw)
    d2 = _parse_date(d2_raw)

    query = (
        ParteDiaria.query.options(
            joinedload(ParteDiaria.equipo),
            joinedload(ParteDiaria.operador),
        )
    )
    if d1:
        query = query.filter(ParteDiaria.fecha >= d1)
    if d2:
        query = query.filter(ParteDiaria.fecha <= d2)
    if q:
        like = f"%{q}%"
        query = query.join(Equipo).filter(
            or_(Equipo.codigo.ilike(like), Equipo.tipo.ilike(like))
        )

    query = query.order_by(ParteDiaria.fecha.desc(), ParteDiaria.id.desc())
    page = request.args.get("page", type=int) or 1
    per_page = min(max(request.args.get("per_page", type=int) or 20, 1), 100)
    rows, pagination = paginate(query, page=page, per_page=per_page)

    total_horas = sum((r.horas_trabajadas or 0.0) for r in rows)
    total_comb = sum((r.combustible_l or 0.0) for r in rows)

    return render_template(
        "partes/index.html",
        rows=rows,
        q=q,
        d1=d1_raw,
        d2=d2_raw,
        total_horas=total_horas,
        total_comb=total_comb,
        pagination=pagination,
    )


@bp.get("/nuevo")
@login_required
def nuevo():
    equipos = Equipo.query.order_by(Equipo.codigo).all()
    operadores = Operador.query.order_by(Operador.nombre).all() if Operador else []
    hoy = date.today().isoformat()
    pre = {
        "fecha": request.args.get("fecha") or hoy,
        "equipo_id": request.args.get("equipo_id"),
        "operador_id": request.args.get("operador_id"),
        "turno": request.args.get("turno") or "matutino",
        "ubicacion": request.args.get("ubicacion"),
        "clima": request.args.get("clima"),
        "horas_inicio": request.args.get("horas_inicio"),
        "horas_fin": request.args.get("horas_fin"),
        "combustible_l": request.args.get("combustible_l"),
        "observaciones": request.args.get("observaciones"),
    }
    return render_template(
        "partes/nuevo.html",
        equipos=equipos,
        operadores=operadores,
        hoy=hoy,
        pre=pre,
    )


@bp.post("/crear")
@login_required
def crear():
    equipo_id = request.form.get("equipo_id")
    if not equipo_id:
        flash("Selecciona un equipo.", "error")
        return redirect(url_for("partes.nuevo"))

    data = {
        "fecha": _parse_date(request.form.get("fecha")) or date.today(),
        "equipo_id": int(equipo_id),
        "operador_id": int(request.form.get("operador_id"))
        if request.form.get("operador_id")
        else None,
        "turno": request.form.get("turno") or "matutino",
        "ubicacion": request.form.get("ubicacion"),
        "clima": request.form.get("clima"),
        "horas_inicio": _parse_float(request.form.get("horas_inicio")),
        "horas_fin": _parse_float(request.form.get("horas_fin")),
        "combustible_l": _parse_float(request.form.get("combustible_l")),
        "observaciones": request.form.get("observaciones"),
    }

    parte = ParteDiaria(**data)
    parte.actualizar_horas_trabajadas()
    db.session.add(parte)
    db.session.commit()
    flash("Parte diaria creada", "success")
    return redirect(url_for("partes.editar", parte_id=parte.id))


@bp.get("/<int:parte_id>/editar")
@login_required
def editar(parte_id: int):
    parte = (
        ParteDiaria.query.options(
            joinedload(ParteDiaria.actividades),
            joinedload(ParteDiaria.equipo),
            joinedload(ParteDiaria.operador),
        ).get_or_404(parte_id)
    )
    actividades = parte.actividades
    operadores = Operador.query.order_by(Operador.nombre).all() if Operador else []
    equipos = Equipo.query.order_by(Equipo.codigo).all()
    return render_template(
        "partes/editar.html",
        p=parte,
        actividades=actividades,
        operadores=operadores,
        equipos=equipos,
    )


@bp.post("/<int:parte_id>/agregar_actividad")
@login_required
def agregar_actividad(parte_id: int):
    parte = ParteDiaria.query.get_or_404(parte_id)
    actividad = ActividadDiaria(
        parte_id=parte.id,
        descripcion=request.form.get("descripcion") or "Actividad",
        cantidad=_parse_float(request.form.get("cantidad")),
        unidad=request.form.get("unidad"),
        horas=_parse_float(request.form.get("horas")),
        notas=request.form.get("notas"),
    )
    db.session.add(actividad)
    db.session.commit()
    flash("Actividad agregada", "success")
    return redirect(url_for("partes.editar", parte_id=parte.id))


@bp.post("/<int:parte_id>/eliminar_actividad/<int:act_id>")
@login_required
def eliminar_actividad(parte_id: int, act_id: int):
    actividad = ActividadDiaria.query.get_or_404(act_id)
    db.session.delete(actividad)
    db.session.commit()
    flash("Actividad eliminada", "success")
    return redirect(url_for("partes.editar", parte_id=parte_id))


@bp.post("/<int:parte_id>/actualizar")
@login_required
def actualizar(parte_id: int):
    parte = ParteDiaria.query.get_or_404(parte_id)

    for key in ["fecha", "turno", "ubicacion", "clima", "observaciones"]:
        if key == "fecha":
            fecha_val = _parse_date(request.form.get(key))
            if fecha_val:
                setattr(parte, key, fecha_val)
            continue
        value = request.form.get(key)
        if value is not None:
            setattr(parte, key, value or None)

    parte.horas_inicio = _parse_float(request.form.get("horas_inicio"))
    parte.horas_fin = _parse_float(request.form.get("horas_fin"))
    parte.horas_trabajadas = _parse_float(request.form.get("horas_trabajadas"))
    parte.combustible_l = _parse_float(request.form.get("combustible_l"))

    equipo_id = request.form.get("equipo_id")
    if equipo_id:
        parte.equipo_id = int(equipo_id)
    operador_id = request.form.get("operador_id")
    parte.operador_id = int(operador_id) if operador_id else None

    if parte.horas_trabajadas is None:
        parte.actualizar_horas_trabajadas()

    db.session.commit()
    flash("Parte actualizada", "success")
    return redirect(url_for("partes.detalle", parte_id=parte.id))


@bp.post("/<int:parte_id>/eliminar")
@login_required
def eliminar(parte_id: int):
    parte = ParteDiaria.query.get_or_404(parte_id)
    db.session.delete(parte)
    db.session.commit()
    flash("Parte eliminada", "success")
    return redirect(url_for("partes.index"))


@bp.get("/<int:parte_id>")
@login_required
def detalle(parte_id: int):
    parte = (
        ParteDiaria.query.options(
            joinedload(ParteDiaria.actividades),
            joinedload(ParteDiaria.equipo),
            joinedload(ParteDiaria.operador),
        ).get_or_404(parte_id)
    )
    actividades = parte.actividades
    total_horas_acts = sum((a.horas or 0.0) for a in actividades)
    total_prod = sum((a.cantidad or 0.0) for a in actividades)
    return render_template(
        "partes/detalle.html",
        p=parte,
        actividades=actividades,
        total_horas_acts=total_horas_acts,
        total_prod=total_prod,
    )


@bp.get("/export.csv")
@login_required
def export_csv():
    d1_raw = request.args.get("d1")
    d2_raw = request.args.get("d2")
    q = (request.args.get("q") or "").strip()

    d1 = _parse_date(d1_raw)
    d2 = _parse_date(d2_raw)

    query = ParteDiaria.query.options(
        joinedload(ParteDiaria.equipo), joinedload(ParteDiaria.operador)
    )
    if d1:
        query = query.filter(ParteDiaria.fecha >= d1)
    if d2:
        query = query.filter(ParteDiaria.fecha <= d2)
    if q:
        like = f"%{q}%"
        query = query.join(Equipo).filter(
            or_(Equipo.codigo.ilike(like), Equipo.tipo.ilike(like))
        )

    rows = query.order_by(ParteDiaria.fecha.asc()).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "fecha",
            "equipo_codigo",
            "equipo_id",
            "operador_nombre",
            "operador_id",
            "turno",
            "ubicacion",
            "clima",
            "horas_inicio",
            "horas_fin",
            "horas_trabajadas",
            "combustible_l",
            "observaciones",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.fecha.isoformat() if row.fecha else "",
                row.equipo.codigo if row.equipo else "",
                row.equipo_id,
                row.operador.nombre if row.operador else "",
                row.operador_id or "",
                row.turno,
                row.ubicacion or "",
                row.clima or "",
                row.horas_inicio or "",
                row.horas_fin or "",
                row.horas_trabajadas or "",
                row.combustible_l or "",
                (row.observaciones or "").replace("\n", " "),
            ]
        )

    buf.seek(0)
    return send_file(
        io.BytesIO(buf.read().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="partes_diarias.csv",
    )
