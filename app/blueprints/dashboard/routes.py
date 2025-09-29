from datetime import date, timedelta
from flask import Blueprint, render_template, current_app
from sqlalchemy import func
from app.extensions import db

bp = Blueprint("dashboard_bp", __name__, url_prefix="/dashboard", template_folder="../../templates/dashboard")

@bp.before_request
def _guard():
    # En DEV no bloqueamos
    if current_app.config.get("SECURITY_DISABLED") or current_app.config.get("LOGIN_DISABLED"):
        return

def _safe_imports():
    # Importa modelos si existen (tolerante)
    try:
        from app.models.equipo import Equipo
    except Exception:
        try:
            from app.models import Equipo
        except Exception:
            Equipo = None
    try:
        from app.models.operador import Operador
    except Exception:
        try:
            from app.models import Operador
        except Exception:
            Operador = None
    try:
        from app.models.parte_diaria import ParteDiaria
    except Exception:
        ParteDiaria = None
    try:
        from app.models.checklist import ChecklistTemplate, ChecklistRun
    except Exception:
        ChecklistTemplate = ChecklistRun = None
    try:
        from app.models.parte_diaria import ArchivoAdjunto
    except Exception:
        try:
            from app.models.archivo import ArchivoAdjunto
        except Exception:
            ArchivoAdjunto = None
    return Equipo, Operador, ParteDiaria, ChecklistTemplate, ChecklistRun, ArchivoAdjunto

def _date_list(days):
    # últimos N días, ascendente
    return [date.today() - timedelta(days=i) for i in range(days-1, -1, -1)]

@bp.get("/")
def index():
    Equipo, Operador, ParteDiaria, ChecklistTemplate, ChecklistRun, ArchivoAdjunto = _safe_imports()

    # --------- KPIs (conteos) ---------
    def _count(model):
        try:
            return int(db.session.query(func.count(model.id)).scalar() or 0)
        except Exception:
            return "-"

    counts = {
        "equipos": _count(Equipo) if Equipo else "-",
        "operadores": _count(Operador) if Operador else "-",
        "partes": _count(ParteDiaria) if ParteDiaria else "-",
        "plantillas": _count(ChecklistTemplate) if ChecklistTemplate else "-",
        "checklist_runs": _count(ChecklistRun) if ChecklistRun else "-",
        "archivos": _count(ArchivoAdjunto) if ArchivoAdjunto else "-",
    }

    # --------- Series: últimos 14 días ---------
    labels_14 = [d.isoformat() for d in _date_list(14)]

    horas_14 = [0.0] * 14
    if ParteDiaria:
        start14 = date.today() - timedelta(days=13)
        rows = (db.session.query(ParteDiaria.fecha, func.coalesce(func.sum(ParteDiaria.horas_trabajo), 0.0))
                .filter(ParteDiaria.fecha >= start14)
                .group_by(ParteDiaria.fecha)
                .order_by(ParteDiaria.fecha)
                .all())
        idx = {lab: i for i, lab in enumerate(labels_14)}
        for f, s in rows:
            k = f.isoformat()
            if k in idx:
                horas_14[idx[k]] = float(s or 0.0)

    pctok_14 = [0.0] * 14
    if ChecklistRun:
        start14 = date.today() - timedelta(days=13)
        rows = (db.session.query(ChecklistRun.fecha, func.coalesce(func.avg(ChecklistRun.pct_ok), 0.0))
                .filter(ChecklistRun.fecha >= start14)
                .group_by(ChecklistRun.fecha)
                .order_by(ChecklistRun.fecha)
                .all())
        idx = {lab: i for i, lab in enumerate(labels_14)}
        for f, avgv in rows:
            k = f.isoformat()
            if k in idx:
                pctok_14[idx[k]] = float(avgv or 0.0)

    # --------- Top 5 equipos por horas (30 días) ---------
    top_labels, top_data = [], []
    if ParteDiaria:
        start30 = date.today() - timedelta(days=29)
        if Equipo:
            rows = (db.session.query(func.coalesce(Equipo.nombre, func.concat("Equipo #", Equipo.id)), func.sum(ParteDiaria.horas_trabajo))
                    .join(Equipo, Equipo.id == ParteDiaria.equipo_id, isouter=True)
                    .filter(ParteDiaria.fecha >= start30, ParteDiaria.equipo_id != None)
                    .group_by(Equipo.id, Equipo.nombre)
                    .order_by(func.sum(ParteDiaria.horas_trabajo).desc())
                    .limit(5).all())
        else:
            rows = (db.session.query(ParteDiaria.equipo_id, func.sum(ParteDiaria.horas_trabajo))
                    .filter(ParteDiaria.fecha >= start30, ParteDiaria.equipo_id != None)
                    .group_by(ParteDiaria.equipo_id)
                    .order_by(func.sum(ParteDiaria.horas_trabajo).desc())
                    .limit(5).all())
            rows = [(f"Equipo #{eid or '-'}", s) for eid, s in rows]
        for name, s in rows:
            top_labels.append(str(name))
            top_data.append(float(s or 0.0))

    # --------- Pie: partes con/ sin incidencias (30 días) ---------
    incid_pie = [0, 0]  # [con_incid, sin_incid]
    if ParteDiaria:
        start30 = date.today() - timedelta(days=29)
        total = (db.session.query(func.count(ParteDiaria.id))
                 .filter(ParteDiaria.fecha >= start30).scalar() or 0)
        con = (db.session.query(func.count(ParteDiaria.id))
               .filter(ParteDiaria.fecha >= start30)
               .filter(func.coalesce(func.nullif(func.trim(ParteDiaria.incidencias), ''), None) != None)
               .scalar() or 0)
        incid_pie = [int(con), int(total - con)]

    # Render
    return render_template(
        "dashboard/index.html",
        counts=counts,
        labels_14=labels_14,
        horas_14=horas_14,
        pctok_14=pctok_14,
        top_labels=top_labels,
        top_data=top_data,
        incid_pie=incid_pie,
    )
