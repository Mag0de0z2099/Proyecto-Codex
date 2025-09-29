from datetime import date, timedelta
from io import StringIO, BytesIO
import csv
from flask import Blueprint, render_template, current_app, request, send_file, abort
from sqlalchemy import func
from app.extensions import db

bp = Blueprint("dashboard_bp", __name__, url_prefix="/dashboard", template_folder="../../templates/dashboard")

@bp.before_request
def _guard():
    # En DEV no bloqueamos
    if current_app.config.get("SECURITY_DISABLED") or current_app.config.get("LOGIN_DISABLED"):
        return

def _safe_imports():
    try:
        from app.models.equipo import Equipo
    except Exception:
        try: from app.models import Equipo
        except Exception: Equipo = None
    try:
        from app.models.operador import Operador
    except Exception:
        try: from app.models import Operador
        except Exception: Operador = None
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
        try: from app.models.archivo import ArchivoAdjunto
        except Exception: ArchivoAdjunto = None
    return Equipo, Operador, ParteDiaria, ChecklistTemplate, ChecklistRun, ArchivoAdjunto

def _date_list(days):
    return [date.today() - timedelta(days=i) for i in range(days-1, -1, -1)]

def _valid_days(raw):
    try:
        d = int(raw)
    except Exception:
        return 14
    return d if d in (7,14,30,60,90) else 14

@bp.get("/")
def index():
    Equipo, Operador, ParteDiaria, ChecklistTemplate, ChecklistRun, ArchivoAdjunto = _safe_imports()
    days = _valid_days(request.args.get("days", 14))

    # KPIs
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

    # Series por días seleccionados
    labels = [d.isoformat() for d in _date_list(days)]

    horas_series = [0.0] * days
    if ParteDiaria:
        start = date.today() - timedelta(days=days-1)
        rows = (db.session.query(ParteDiaria.fecha, func.coalesce(func.sum(ParteDiaria.horas_trabajo), 0.0))
                .filter(ParteDiaria.fecha >= start)
                .group_by(ParteDiaria.fecha)
                .order_by(ParteDiaria.fecha)
                .all())
        idx = {lab: i for i, lab in enumerate(labels)}
        for f, s in rows:
            k = f.isoformat()
            if k in idx:
                horas_series[idx[k]] = float(s or 0.0)

    pctok_series = [0.0] * days
    if ChecklistRun:
        start = date.today() - timedelta(days=days-1)
        rows = (db.session.query(ChecklistRun.fecha, func.coalesce(func.avg(ChecklistRun.pct_ok), 0.0))
                .filter(ChecklistRun.fecha >= start)
                .group_by(ChecklistRun.fecha)
                .order_by(ChecklistRun.fecha)
                .all())
        idx = {lab: i for i, lab in enumerate(labels)}
        for f, avgv in rows:
            k = f.isoformat()
            if k in idx:
                pctok_series[idx[k]] = float(avgv or 0.0)

    # Top equipos (usa el mismo 'days')
    top_labels, top_data = [], []
    if ParteDiaria:
        start = date.today() - timedelta(days=days-1)
        if Equipo:
            rows = (db.session.query(func.coalesce(Equipo.nombre, func.concat("Equipo #", Equipo.id)), func.sum(ParteDiaria.horas_trabajo))
                    .join(Equipo, Equipo.id == ParteDiaria.equipo_id, isouter=True)
                    .filter(ParteDiaria.fecha >= start, ParteDiaria.equipo_id != None)
                    .group_by(Equipo.id, Equipo.nombre)
                    .order_by(func.sum(ParteDiaria.horas_trabajo).desc())
                    .limit(5).all())
        else:
            rows = (db.session.query(ParteDiaria.equipo_id, func.sum(ParteDiaria.horas_trabajo))
                    .filter(ParteDiaria.fecha >= start, ParteDiaria.equipo_id != None)
                    .group_by(ParteDiaria.equipo_id)
                    .order_by(func.sum(ParteDiaria.horas_trabajo).desc())
                    .limit(5).all())
            rows = [(f"Equipo #{eid or '-'}", s) for eid, s in rows]
        for name, s in rows:
            top_labels.append(str(name))
            top_data.append(float(s or 0.0))

    # Pie incidencias
    incid_pie = [0, 0]
    incid_daily = []  # para CSV detallado
    if ParteDiaria:
        start = date.today() - timedelta(days=days-1)
        total = (db.session.query(func.count(ParteDiaria.id))
                 .filter(ParteDiaria.fecha >= start).scalar() or 0)
        con = (db.session.query(func.count(ParteDiaria.id))
               .filter(ParteDiaria.fecha >= start)
               .filter(func.coalesce(func.nullif(func.trim(ParteDiaria.incidencias), ''), None) != None)
               .scalar() or 0)
        incid_pie = [int(con), int(total - con)]
        # breakdown diario
        drows = (db.session.query(
                    ParteDiaria.fecha,
                    func.sum(func.case(
                        (func.coalesce(func.nullif(func.trim(ParteDiaria.incidencias), ''), None) != None, 1),
                        else_=0
                    )),
                    func.count(ParteDiaria.id)
                 )
                 .filter(ParteDiaria.fecha >= start)
                 .group_by(ParteDiaria.fecha)
                 .order_by(ParteDiaria.fecha)
                 .all())
        for f, con_d, tot_d in drows:
            incid_daily.append((f.isoformat(), int(con_d or 0), int(tot_d or 0), int((tot_d or 0) - (con_d or 0))))

    return render_template(
        "dashboard/index.html",
        counts=counts,
        labels_14=labels,          # reusamos variables de la plantilla
        horas_14=horas_series,
        pctok_14=pctok_series,
        top_labels=top_labels,
        top_data=top_data,
        incid_pie=incid_pie,
        days=days
    )

# ----------------- CSV Exports -----------------

def _csv_bytes(rows, header):
    buf = StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    for r in rows: w.writerow(r)
    data = buf.getvalue().encode("utf-8")
    return BytesIO(data)

@bp.get("/export/kpis.csv")
def export_kpis():
    Equipo, Operador, ParteDiaria, ChecklistTemplate, ChecklistRun, ArchivoAdjunto = _safe_imports()
    def _count(m):
        try: return int(db.session.query(func.count(m.id)).scalar() or 0)
        except: return 0
    rows = [("equipos", _count(Equipo) if Equipo else 0),
            ("operadores", _count(Operador) if Operador else 0),
            ("partes", _count(ParteDiaria) if ParteDiaria else 0),
            ("plantillas", _count(ChecklistTemplate) if ChecklistTemplate else 0),
            ("checklist_runs", _count(ChecklistRun) if ChecklistRun else 0),
            ("archivos", _count(ArchivoAdjunto) if ArchivoAdjunto else 0)]
    bio = _csv_bytes(rows, ["kpi","valor"])
    return send_file(bio, as_attachment=True, download_name="dashboard_kpis.csv", mimetype="text/csv")

@bp.get("/export/series.csv")
def export_series():
    metric = request.args.get("metric", "horas")  # 'horas' | 'pctok'
    days = _valid_days(request.args.get("days", 14))
    _, _, ParteDiaria, _, ChecklistRun, _ = _safe_imports()
    labels = [d.isoformat() for d in _date_list(days)]
    rows = []
    if metric == "horas" and ParteDiaria:
        start = date.today() - timedelta(days=days-1)
        data = {lab: 0.0 for lab in labels}
        q = (db.session.query(ParteDiaria.fecha, func.coalesce(func.sum(ParteDiaria.horas_trabajo), 0.0))
             .filter(ParteDiaria.fecha >= start).group_by(ParteDiaria.fecha).all())
        for f, s in q: data[f.isoformat()] = float(s or 0.0)
        rows = [(k, data[k]) for k in labels]
    elif metric == "pctok" and ChecklistRun:
        start = date.today() - timedelta(days=days-1)
        data = {lab: 0.0 for lab in labels}
        q = (db.session.query(ChecklistRun.fecha, func.coalesce(func.avg(ChecklistRun.pct_ok), 0.0))
             .filter(ChecklistRun.fecha >= start).group_by(ChecklistRun.fecha).all())
        for f, s in q: data[f.isoformat()] = float(s or 0.0)
        rows = [(k, data[k]) for k in labels]
    else:
        rows = [(lab, 0) for lab in labels]
    bio = _csv_bytes(rows, ["fecha", metric])
    return send_file(bio, as_attachment=True, download_name=f"series_{metric}_{days}d.csv", mimetype="text/csv")

@bp.get("/export/top_equipos.csv")
def export_top_equipos():
    days = _valid_days(request.args.get("days", 14))
    Equipo, _, ParteDiaria, *_ = _safe_imports()
    start = date.today() - timedelta(days=days-1)
    rows = []
    if ParteDiaria:
        if Equipo:
            q = (db.session.query(func.coalesce(Equipo.nombre, func.concat("Equipo #", Equipo.id)), func.sum(ParteDiaria.horas_trabajo))
                 .join(Equipo, Equipo.id == ParteDiaria.equipo_id, isouter=True)
                 .filter(ParteDiaria.fecha >= start, ParteDiaria.equipo_id != None)
                 .group_by(Equipo.id, Equipo.nombre)
                 .order_by(func.sum(ParteDiaria.horas_trabajo).desc()).limit(5).all())
        else:
            q = (db.session.query(ParteDiaria.equipo_id, func.sum(ParteDiaria.horas_trabajo))
                 .filter(ParteDiaria.fecha >= start, ParteDiaria.equipo_id != None)
                 .group_by(ParteDiaria.equipo_id)
                 .order_by(func.sum(ParteDiaria.horas_trabajo).desc()).limit(5).all())
            q = [(f"Equipo #{eid or '-'}", s) for eid, s in q]
        rows = [(name, float(s or 0.0)) for name, s in q]
    bio = _csv_bytes(rows, ["equipo","horas"])
    return send_file(bio, as_attachment=True, download_name=f"top_equipos_{days}d.csv", mimetype="text/csv")

@bp.get("/export/incidencias.csv")
def export_incidencias():
    days = _valid_days(request.args.get("days", 14))
    _, _, ParteDiaria, *_ = _safe_imports()
    start = date.today() - timedelta(days=days-1)
    rows = []
    if ParteDiaria:
        q = (db.session.query(
                ParteDiaria.fecha,
                func.sum(func.case((func.coalesce(func.nullif(func.trim(ParteDiaria.incidencias), ''), None) != None, 1), else_=0)),
                func.count(ParteDiaria.id)
            )
            .filter(ParteDiaria.fecha >= start)
            .group_by(ParteDiaria.fecha)
            .order_by(ParteDiaria.fecha).all())
        # fecha, con_incidencias, total, sin_incidencias
        for f, con, tot in q:
            rows.append((f.isoformat(), int(con or 0), int(tot or 0), int((tot or 0) - (con or 0))))
    bio = _csv_bytes(rows, ["fecha","con_incidencias","total","sin_incidencias"])
    return send_file(bio, as_attachment=True, download_name=f"incidencias_{days}d.csv", mimetype="text/csv")
