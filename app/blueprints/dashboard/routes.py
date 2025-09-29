from __future__ import annotations

from datetime import date, timedelta

from flask import render_template
from sqlalchemy import func

from app import db
from app.models import Checklist, Equipo, ParteDiaria

try:
    from app.models import Operador
except Exception:  # pragma: no cover - apps sin operadores
    Operador = None

from . import bp


@bp.get("/")
def home():
    hoy = date.today()
    # KPIs
    total_equipos = db.session.scalar(db.select(func.count()).select_from(Equipo))
    total_operadores = (
        db.session.scalar(db.select(func.count()).select_from(Operador)) if Operador else 0
    )

    # Partes de hoy
    q_partes_hoy = db.select(
        func.count(ParteDiaria.id),
        func.coalesce(func.sum(ParteDiaria.horas_trabajo), 0.0),
    ).where(ParteDiaria.fecha == hoy)
    partes_count, horas_hoy = db.session.execute(q_partes_hoy).one()

    # Checklists de hoy
    q_chk_apto = db.select(func.count(Checklist.id)).where(
        Checklist.date == hoy, Checklist.overall_status == "APTO"
    )
    q_chk_no = db.select(func.count(Checklist.id)).where(
        Checklist.date == hoy, Checklist.overall_status == "NO_APTO"
    )
    chk_apto = db.session.scalar(q_chk_apto)
    chk_noapto = db.session.scalar(q_chk_no)

    # Alertas: NO_APTO últimos 3 días
    desde = hoy - timedelta(days=3)
    noaptos = (
        db.session.query(Checklist)
        .filter(Checklist.date >= desde, Checklist.overall_status == "NO_APTO")
        .order_by(Checklist.date.desc())
        .limit(10)
        .all()
    )

    # Partes de hoy con datos faltantes
    partes_incompletos = (
        db.session.query(ParteDiaria)
        .filter(ParteDiaria.fecha == hoy)
        .filter(
            (func.coalesce(ParteDiaria.horas_trabajo, 0) <= 0)
            | (ParteDiaria.actividad.is_(None))
            | (func.length(func.trim(ParteDiaria.actividad)) == 0)
        )
        .order_by(ParteDiaria.id.desc())
        .all()
    )

    return render_template(
        "dashboard/index.html",
        total_equipos=total_equipos,
        total_operadores=total_operadores,
        partes_count=partes_count,
        horas_hoy=horas_hoy,
        chk_apto=chk_apto,
        chk_noapto=chk_noapto,
        noaptos=noaptos,
        partes_incompletos=partes_incompletos,
        hoy=hoy,
    )
