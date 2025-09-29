import os
import csv
from io import BytesIO
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import cm
from sqlalchemy import func
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


def _pdf_header_footer(c, title):
    w, h = LETTER
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, h - 2 * cm, title)
    c.setFont("Helvetica", 8)
    c.drawRightString(w - 2 * cm, 1.5 * cm, datetime.utcnow().strftime("Generado %Y-%m-%d %H:%M UTC"))
    c.line(2 * cm, h - 2.2 * cm, w - 2 * cm, h - 2.2 * cm)


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


@bp.get("/<int:id>/pdf")
def pdf_parte(id):
    p = ParteDiaria.query.get_or_404(id)
    eq_name = f"Equipo #{p.equipo_id}"
    op_name = f"Operador #{p.operador_id}"
    try:
        if p.equipo_id and "Equipo" in globals():
            e = db.session.get(Equipo, p.equipo_id)
            if e and hasattr(e, "nombre"):
                eq_name = f"{getattr(e, 'nombre', eq_name)} (#{e.id})"
    except Exception:
        pass
    try:
        if p.operador_id and "Operador" in globals():
            o = db.session.get(Operador, p.operador_id)
            if o and hasattr(o, "nombre"):
                op_name = f"{getattr(o, 'nombre', op_name)} (#{o.id})"
    except Exception:
        pass

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    _pdf_header_footer(c, "Parte diaria")

    x, y = 2 * cm, 25 * cm
    c.setFont("Helvetica", 10)
    rows = [
        ("ID", p.id),
        ("Fecha", p.fecha.isoformat() if p.fecha else ""),
        ("Equipo", eq_name),
        ("Operador", op_name),
        ("Horas de trabajo", f"{p.horas_trabajo:.2f}"),
        ("Actividad", p.actividad or ""),
        ("Incidencias", p.incidencias or ""),
        ("Notas", p.notas or ""),
    ]
    for k, v in rows:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, f"{k}:")
        c.setFont("Helvetica", 10)
        c.drawString(x + 4.2 * cm, y, str(v))
        y -= 0.9 * cm
        if y < 3 * cm:
            c.showPage()
            _pdf_header_footer(c, "Parte diaria")
            y = 25 * cm

    c.showPage()
    c.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"parte_{p.id}.pdf", mimetype="application/pdf")


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


@bp.get("/resumen")
def resumen():
    desde = _parse_date(request.args.get("desde"))
    hasta = _parse_date(request.args.get("hasta"))
    equipo_id = request.args.get("equipo_id", type=int)

    q = ParteDiaria.query
    if desde:
        q = q.filter(ParteDiaria.fecha >= desde)
    if hasta:
        q = q.filter(ParteDiaria.fecha <= hasta)
    if equipo_id:
        q = q.filter(ParteDiaria.equipo_id == equipo_id)

    total_horas = db.session.query(func.coalesce(func.sum(ParteDiaria.horas_trabajo), 0.0))
    if desde:
        total_horas = total_horas.filter(ParteDiaria.fecha >= desde)
    if hasta:
        total_horas = total_horas.filter(ParteDiaria.fecha <= hasta)
    if equipo_id:
        total_horas = total_horas.filter(ParteDiaria.equipo_id == equipo_id)
    total_horas = float(total_horas.scalar() or 0)

    partes_count = q.count()

    incidencias_count = db.session.query(func.count(ParteDiaria.id))
    incidencias_count = incidencias_count.filter(
        func.coalesce(func.nullif(func.trim(ParteDiaria.incidencias), ""), None) != None
    )
    if desde:
        incidencias_count = incidencias_count.filter(ParteDiaria.fecha >= desde)
    if hasta:
        incidencias_count = incidencias_count.filter(ParteDiaria.fecha <= hasta)
    if equipo_id:
        incidencias_count = incidencias_count.filter(ParteDiaria.equipo_id == equipo_id)
    incidencias_count = incidencias_count.scalar() or 0

    ultimos = q.order_by(ParteDiaria.fecha.desc(), ParteDiaria.id.desc()).limit(20).all()

    equipos = Equipo.query.order_by(Equipo.id.desc()).all() if hasattr(Equipo, "query") else []
    return render_template(
        "partes/resumen.html",
        desde=desde,
        hasta=hasta,
        equipo_id=equipo_id,
        equipos=equipos,
        total_horas=total_horas,
        partes_count=partes_count,
        incidencias_count=incidencias_count,
        ultimos=ultimos,
    )


@bp.get("/resumen.pdf")
def resumen_pdf():
    desde = _parse_date(request.args.get("desde"))
    hasta = _parse_date(request.args.get("hasta"))
    equipo_id = request.args.get("equipo_id", type=int)

    q = ParteDiaria.query
    if desde:
        q = q.filter(ParteDiaria.fecha >= desde)
    if hasta:
        q = q.filter(ParteDiaria.fecha <= hasta)
    if equipo_id:
        q = q.filter(ParteDiaria.equipo_id == equipo_id)
    rows = q.order_by(ParteDiaria.fecha.desc(), ParteDiaria.id.desc()).all()

    total_horas = db.session.query(func.coalesce(func.sum(ParteDiaria.horas_trabajo), 0.0))
    if desde:
        total_horas = total_horas.filter(ParteDiaria.fecha >= desde)
    if hasta:
        total_horas = total_horas.filter(ParteDiaria.fecha <= hasta)
    if equipo_id:
        total_horas = total_horas.filter(ParteDiaria.equipo_id == equipo_id)
    total_horas = float(total_horas.scalar() or 0)
    partes_count = len(rows)
    incidencias_count = len([r for r in rows if (r.incidencias or "").strip()])

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    _pdf_header_footer(c, "Resumen de partes diarias")

    w, h = LETTER
    y = h - 3.2 * cm
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Desde: {desde or '-'}   Hasta: {hasta or '-'}   Equipo: {equipo_id or 'todos'}")
    y -= 0.9 * cm
    c.drawString(
        2 * cm,
        y,
        f"Partes: {partes_count}   Total horas: {total_horas:.2f}   Con incidencias: {incidencias_count}",
    )
    y -= 1.2 * cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, y, "Últimos registros")
    y -= 0.7 * cm
    c.setFont("Helvetica", 9)

    for r in rows[:30]:
        line = (
            f"{r.fecha} | Eq:{r.equipo_id or '-'} | Op:{r.operador_id or '-'} | Horas:{r.horas_trabajo:.2f} | "
            f"{(r.actividad or '')[:60]}"
        )
        c.drawString(2 * cm, y, line)
        y -= 0.55 * cm
        if y < 2.5 * cm:
            c.showPage()
            _pdf_header_footer(c, "Resumen de partes diarias")
            y = h - 3 * cm

    c.showPage()
    c.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="resumen_partes.pdf", mimetype="application/pdf")
