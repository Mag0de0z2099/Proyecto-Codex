from __future__ import annotations

import os
import uuid

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import login_required
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from app.db import db
from app.models import (
    AnswerEnum,
    Checklist,
    ChecklistAnswer,
    ChecklistItem,
    ChecklistTemplate,
    Equipo,
    ParteDiaria,
)

try:  # pragma: no cover - módulo opcional
    from app.models import Operador
except Exception:  # pragma: no cover - fallback si no existe
    Operador = None  # type: ignore[assignment]

from . import bp


def pick_template_for_equipment(equipo: Equipo) -> ChecklistTemplate | None:
    tipo = (equipo.tipo or "").lower()
    for template in ChecklistTemplate.query.order_by(ChecklistTemplate.name).all():
        tokens = [token.strip() for token in template.applies_to.lower().split("|")]
        if any(token and token in tipo for token in tokens):
            return template
    return ChecklistTemplate.query.order_by(ChecklistTemplate.name).first()


@bp.get("/")
@login_required
def index():
    q = (request.args.get("q") or "").strip()
    query = Checklist.query
    if q:
        like = f"%{q}%"
        query = query.join(Equipo).filter(
            or_(Equipo.codigo.ilike(like), Equipo.tipo.ilike(like))
        )
    rows = query.order_by(Checklist.created_at.desc()).limit(200).all()
    return render_template("checklists/index.html", rows=rows, q=q)


def _parte_existente_para_checklist(cl_id: int) -> ParteDiaria | None:
    return ParteDiaria.query.filter_by(checklist_id=cl_id).first()


@bp.get("/nuevo")
@login_required
def nuevo():
    equipos = Equipo.query.order_by(Equipo.codigo).all()
    operadores = Operador.query.order_by(Operador.nombre).all() if Operador else []
    templates = ChecklistTemplate.query.order_by(ChecklistTemplate.name).all()
    return render_template(
        "checklists/nuevo.html",
        equipos=equipos,
        operadores=operadores,
        templates=templates,
    )


@bp.post("/crear")
@login_required
def crear():
    equipment_id = int(request.form["equipment_id"])
    template_id = int(request.form.get("template_id") or 0)
    equipo = Equipo.query.get_or_404(equipment_id)
    template = (
        ChecklistTemplate.query.get(template_id)
        if template_id
        else pick_template_for_equipment(equipo)
    )
    if not template:
        flash("No hay plantillas disponibles", "warning")
        return redirect(url_for("checklists.nuevo"))

    cl = Checklist(
        template_id=template.id,
        equipment_id=equipo.id,
        operator_id=(
            int(request.form["operator_id"])
            if request.form.get("operator_id")
            else None
        ),
        shift=request.form.get("shift") or "matutino",
        location=request.form.get("location"),
        weather=request.form.get("weather"),
        hours_start=
            float(request.form["hours_start"]) if request.form.get("hours_start") else None,
        hours_end=
            float(request.form["hours_end"]) if request.form.get("hours_end") else None,
        notes=request.form.get("notes"),
    )
    db.session.add(cl)
    db.session.flush()

    for item in template.items:
        db.session.add(
            ChecklistAnswer(checklist_id=cl.id, item_id=item.id, result=AnswerEnum.OK)
        )

    db.session.commit()
    return redirect(url_for("checklists.editar", cl_id=cl.id))


@bp.get("/<int:cl_id>/editar")
@login_required
def editar(cl_id: int):
    cl = Checklist.query.get_or_404(cl_id)
    items: dict[str, list[ChecklistItem]] = {}
    for item in cl.template.items:
        items.setdefault(item.section, []).append(item)
    for section_items in items.values():
        section_items.sort(key=lambda x: x.order)
    answers = {answer.item_id: answer for answer in cl.answers}
    return render_template(
        "checklists/editar.html",
        cl=cl,
        items_by_section=items,
        answers=answers,
        AnswerEnum=AnswerEnum,
    )


@bp.post("/<int:cl_id>/guardar")
@login_required
def guardar(cl_id: int):
    cl = Checklist.query.get_or_404(cl_id)
    critical_fail = False
    for item in cl.template.items:
        value = request.form.get(f"item_{item.id}") or AnswerEnum.OK.value
        note = request.form.get(f"note_{item.id}") or None
        answer = next((a for a in cl.answers if a.item_id == item.id), None)
        if not answer:
            answer = ChecklistAnswer(checklist_id=cl.id, item_id=item.id)
            db.session.add(answer)
        answer.result = AnswerEnum(value)
        answer.note = note

        file = request.files.get(f"photo_{item.id}")
        if file and file.filename:
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            filepath = os.path.join(current_app.config["UPLOAD_CHECKLISTS_DIR"], filename)
            file.save(filepath)
            answer.photo_path = filename
        if item.critical and answer.result == AnswerEnum.FAIL:
            critical_fail = True

    cl.overall_status = "NO_APTO" if critical_fail else "APTO"
    db.session.commit()
    flash("Checklist guardado", "success")
    return redirect(url_for("checklists.detalle", cl_id=cl.id))


@bp.post("/<int:cl_id>/generar_parte")
@login_required
def generar_parte(cl_id: int):
    cl = Checklist.query.get_or_404(cl_id)
    existente = _parte_existente_para_checklist(cl.id)
    if existente:
        flash("Este checklist ya tiene un parte generado.", "info")
        return redirect(url_for("partes.editar", parte_id=existente.id))

    horas_trabajadas = None
    if (
        cl.hours_start is not None
        and cl.hours_end is not None
        and cl.hours_end >= cl.hours_start
    ):
        horas_trabajadas = cl.hours_end - cl.hours_start

    parte = ParteDiaria(
        fecha=cl.date,
        equipo_id=cl.equipment_id,
        operador_id=cl.operator_id,
        turno=cl.shift or "matutino",
        ubicacion=cl.location,
        clima=cl.weather,
        horas_inicio=cl.hours_start,
        horas_fin=cl.hours_end,
        horas_trabajadas=horas_trabajadas,
        observaciones=cl.notes or "",
        checklist_id=cl.id,
    )
    db.session.add(parte)
    db.session.commit()
    flash("Parte diario generado desde el checklist.", "success")
    return redirect(url_for("partes.editar", parte_id=parte.id))


@bp.get("/<int:cl_id>")
@login_required
def detalle(cl_id: int):
    cl = Checklist.query.get_or_404(cl_id)
    items: dict[str, list[ChecklistItem]] = {}
    for item in cl.template.items:
        items.setdefault(item.section, []).append(item)
    for section_items in items.values():
        section_items.sort(key=lambda x: x.order)
    answers = {answer.item_id: answer for answer in cl.answers}
    return render_template(
        "checklists/detalle.html",
        cl=cl,
        items_by_section=items,
        answers=answers,
        parte=_parte_existente_para_checklist(cl.id),
    )


@bp.get("/photo/<path:fname>")
@login_required
def photo(fname: str):
    return send_from_directory(
        current_app.config["UPLOAD_CHECKLISTS_DIR"], fname, as_attachment=False
    )
