from datetime import datetime, date
from io import BytesIO

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_file,
)
from sqlalchemy import func
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import cm

from app.extensions import db
from app.models.checklist import (
    ChecklistTemplate,
    ChecklistItem,
    ChecklistRun,
    ChecklistAnswer,
)

try:
    from app.models.equipo import Equipo
except Exception:  # pragma: no cover - módulo opcional
    Equipo = None
try:
    from app.models.operador import Operador
except Exception:  # pragma: no cover - módulo opcional
    Operador = None

bp = Blueprint(
    "checklists_bp",
    __name__,
    url_prefix="/checklists",
    template_folder="../../templates/checklists",
)


@bp.before_request
def _guard():
    if current_app.config.get("SECURITY_DISABLED") or current_app.config.get("LOGIN_DISABLED"):
        return


def _parse_date(s, default=None):
    if not s:
        return default
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:  # pragma: no cover - validaciones
        return default


def _pdf_header_footer(c, title):
    w, h = LETTER
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, h - 2 * cm, title)
    c.setFont("Helvetica", 8)
    c.drawRightString(
        w - 2 * cm,
        1.5 * cm,
        datetime.utcnow().strftime("Generado %Y-%m-%d %H:%M UTC"),
    )
    c.line(2 * cm, h - 2.2 * cm, w - 2 * cm, h - 2.2 * cm)


@bp.get("/templates")
def templates_index():
    rows = ChecklistTemplate.query.order_by(ChecklistTemplate.id.desc()).all()
    return render_template("checklists/templates_index.html", rows=rows)


@bp.get("/")
def root_redirect():
    return redirect(url_for("checklists_bp.templates_index"))


@bp.route("/templates/new", methods=["GET", "POST"])
def template_new():
    if request.method == "POST":
        t = ChecklistTemplate(
            nombre=(request.form.get("nombre") or "").strip(),
            norma=(request.form.get("norma") or "").strip(),
        )
        db.session.add(t)
        db.session.commit()
        flash("Plantilla creada", "success")
        return redirect(url_for("checklists_bp.templates_index"))
    return render_template("checklists/template_form.html", item=None)


@bp.route("/templates/<int:id>/edit", methods=["GET", "POST"])
def template_edit(id):
    t = ChecklistTemplate.query.get_or_404(id)
    if request.method == "POST":
        t.nombre = (request.form.get("nombre") or "").strip()
        t.norma = (request.form.get("norma") or "").strip()
        db.session.commit()
        flash("Plantilla actualizada", "success")
        return redirect(url_for("checklists_bp.templates_index"))
    items = t.items.order_by(ChecklistItem.orden.asc(), ChecklistItem.id.asc()).all()
    return render_template("checklists/template_form.html", item=t, items=items)


@bp.post("/templates/<int:id>/delete")
def template_delete(id):
    t = ChecklistTemplate.query.get_or_404(id)
    db.session.delete(t)
    db.session.commit()
    flash("Plantilla eliminada", "success")
    return redirect(url_for("checklists_bp.templates_index"))


@bp.post("/templates/<int:id>/items/add")
def template_item_add(id):
    t = ChecklistTemplate.query.get_or_404(id)
    texto = (request.form.get("texto") or "").strip()
    tipo = request.form.get("tipo") or "bool"
    orden = request.form.get("orden", type=int) or 0
    if not texto:
        flash("Texto requerido", "warning")
        return redirect(url_for("checklists_bp.template_edit", id=id))
    db.session.add(
        ChecklistItem(template_id=t.id, texto=texto, tipo=tipo, orden=orden)
    )
    db.session.commit()
    flash("Ítem agregado", "success")
    return redirect(url_for("checklists_bp.template_edit", id=id))


@bp.post("/templates/<int:template_id>/items/<int:item_id>/delete")
def template_item_delete(template_id, item_id):
    it = ChecklistItem.query.get_or_404(item_id)
    db.session.delete(it)
    db.session.commit()
    flash("Ítem eliminado", "success")
    return redirect(url_for("checklists_bp.template_edit", id=template_id))


@bp.route("/ejecutar", methods=["GET", "POST"])
def ejecutar():
    if request.method == "GET" and not request.args.get("template_id"):
        templates = ChecklistTemplate.query.order_by(ChecklistTemplate.nombre.asc()).all()
        equipos = Equipo.query.all() if Equipo else []
        operadores = Operador.query.all() if Operador else []
        return render_template(
            "checklists/ejecutar_select.html",
            templates=templates,
            equipos=equipos,
            operadores=operadores,
        )

    template_id = request.values.get("template_id", type=int)
    t = ChecklistTemplate.query.get_or_404(template_id)
    if request.method == "GET":
        items = t.items.order_by(ChecklistItem.orden.asc(), ChecklistItem.id.asc()).all()
        equipos = Equipo.query.all() if Equipo else []
        operadores = Operador.query.all() if Operador else []
        return render_template(
            "checklists/ejecutar_form.html",
            t=t,
            items=items,
            equipos=equipos,
            operadores=operadores,
        )

    fecha = _parse_date(request.form.get("fecha"), default=date.today())
    equipo_id = request.form.get("equipo_id", type=int)
    operador_id = request.form.get("operador_id", type=int)
    notas = (request.form.get("notas") or "").strip()

    run = ChecklistRun(
        template_id=template_id,
        fecha=fecha,
        equipo_id=equipo_id,
        operador_id=operador_id,
        notas=notas,
    )
    db.session.add(run)
    db.session.flush()

    items = ChecklistItem.query.filter_by(template_id=template_id).all()
    oks = 0
    total_bool = 0
    for it in items:
        if it.tipo == "bool":
            total_bool += 1
            val = request.form.get(f"item_{it.id}") == "on"
            if val:
                oks += 1
            db.session.add(
                ChecklistAnswer(
                    run_id=run.id,
                    item_id=it.id,
                    valor_bool=val,
                    comentario=(request.form.get(f"c_{it.id}") or "").strip(),
                )
            )
        else:
            txt = (request.form.get(f"item_{it.id}") or "").strip()
            db.session.add(
                ChecklistAnswer(
                    run_id=run.id,
                    item_id=it.id,
                    valor_bool=None,
                    comentario=txt,
                )
            )
    run.pct_ok = (oks / total_bool * 100.0) if total_bool else 0.0
    db.session.commit()
    flash("Checklist ejecutado", "success")
    return redirect(url_for("checklists_bp.run_view", id=run.id))


@bp.get("/runs")
def runs_index():
    desde = _parse_date(request.args.get("desde"))
    hasta = _parse_date(request.args.get("hasta"))
    q = ChecklistRun.query
    if desde:
        q = q.filter(ChecklistRun.fecha >= desde)
    if hasta:
        q = q.filter(ChecklistRun.fecha <= hasta)
    pag = q.order_by(ChecklistRun.fecha.desc(), ChecklistRun.id.desc()).paginate(
        page=request.args.get("page", 1, type=int),
        per_page=10,
        error_out=False,
    )
    return render_template(
        "checklists/runs_index.html",
        pagination=pag,
        rows=pag.items,
        desde=desde,
        hasta=hasta,
    )


@bp.get("/run/<int:id>")
def run_view(id):
    r = ChecklistRun.query.get_or_404(id)
    items = (
        ChecklistItem.query.filter_by(template_id=r.template_id)
        .order_by(ChecklistItem.orden.asc(), ChecklistItem.id.asc())
        .all()
    )
    answers = {a.item_id: a for a in r.answers.all()}
    return render_template(
        "checklists/run_view.html",
        r=r,
        items=items,
        answers=answers,
    )


@bp.get("/run/<int:id>/pdf")
def run_pdf(id):
    r = ChecklistRun.query.get_or_404(id)
    items = (
        ChecklistItem.query.filter_by(template_id=r.template_id)
        .order_by(ChecklistItem.orden.asc(), ChecklistItem.id.asc())
        .all()
    )
    answers = {a.item_id: a for a in r.answers.all()}

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    _pdf_header_footer(c, f"Checklist — {r.template.nombre}")

    w, h = LETTER
    x, y = 2 * cm, h - 3.2 * cm
    c.setFont("Helvetica", 10)
    header = [
        ("Fecha", r.fecha.isoformat()),
        ("Plantilla", r.template.nombre),
        ("Norma", r.template.norma or "-"),
        ("Equipo", r.equipo_id or "-"),
        ("Operador", r.operador_id or "-"),
        ("% OK", f"{r.pct_ok:.1f}%"),
    ]
    for k, v in header:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, k + ":")
        c.setFont("Helvetica", 10)
        c.drawString(x + 4 * cm, y, str(v))
        y -= 0.8 * cm

    y -= 0.2 * cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, "Resultados")
    y -= 0.7 * cm
    c.setFont("Helvetica", 9)
    for it in items:
        ans = answers.get(it.id)
        if it.tipo == "bool":
            txt = "✓" if (ans and ans.valor_bool) else "✗"
            if ans and ans.comentario:
                txt += f" — {ans.comentario}"
        else:
            txt = ans.comentario if ans else ""
        c.drawString(x, y, f"- {it.texto[:80]}: {txt[:80]}")
        y -= 0.55 * cm
        if y < 2.5 * cm:
            c.showPage()
            _pdf_header_footer(c, f"Checklist — {r.template.nombre}")
            y = h - 3 * cm

    c.showPage()
    c.save()
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"checklist_{r.id}.pdf",
        mimetype="application/pdf",
    )


@bp.get("/resumen")
def resumen():
    desde = _parse_date(request.args.get("desde"))
    hasta = _parse_date(request.args.get("hasta"))
    q = ChecklistRun.query
    if desde:
        q = q.filter(ChecklistRun.fecha >= desde)
    if hasta:
        q = q.filter(ChecklistRun.fecha <= hasta)
    total = q.count()
    avg_ok = db.session.query(func.coalesce(func.avg(ChecklistRun.pct_ok), 0)).scalar() or 0
    ultimos = (
        q.order_by(ChecklistRun.fecha.desc(), ChecklistRun.id.desc())
        .limit(20)
        .all()
    )
    return render_template(
        "checklists/resumen.html",
        total=total,
        avg_ok=avg_ok,
        ultimos=ultimos,
        desde=desde,
        hasta=hasta,
    )


@bp.get("/resumen.pdf")
def resumen_pdf():
    desde = _parse_date(request.args.get("desde"))
    hasta = _parse_date(request.args.get("hasta"))
    q = ChecklistRun.query
    if desde:
        q = q.filter(ChecklistRun.fecha >= desde)
    if hasta:
        q = q.filter(ChecklistRun.fecha <= hasta)
    rows = q.order_by(ChecklistRun.fecha.desc(), ChecklistRun.id.desc()).all()
    total = len(rows)
    avg_ok = sum(r.pct_ok for r in rows) / total if total else 0

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    _pdf_header_footer(c, "Resumen de checklists")

    w, h = LETTER
    y = h - 3.2 * cm
    c.setFont("Helvetica", 10)
    c.drawString(
        2 * cm,
        y,
        f"Desde: {desde or '-'}  Hasta: {hasta or '-'}  Ejecutados: {total}  Promedio OK: {avg_ok:.1f}%",
    )
    y -= 1.2 * cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2 * cm, y, "Últimos")
    y -= 0.7 * cm
    c.setFont("Helvetica", 9)
    for r in rows[:30]:
        line = (
            f"{r.fecha} | T:{r.template.nombre[:20]} | Eq:{r.equipo_id or '-'} | %OK:{r.pct_ok:.1f}"
        )
        c.drawString(2 * cm, y, line)
        y -= 0.55 * cm
        if y < 2.5 * cm:
            c.showPage()
            _pdf_header_footer(c, "Resumen de checklists")
            y = h - 3 * cm
    c.showPage()
    c.save()
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="resumen_checklists.pdf",
        mimetype="application/pdf",
    )
