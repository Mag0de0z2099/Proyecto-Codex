from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy.dialects.postgresql import ENUM as PGEnum

from app.db import db


class AnswerEnum(str, Enum):
    OK = "OK"
    FAIL = "FAIL"
    NA = "NA"


class ChecklistTemplate(db.Model):
    __tablename__ = "cl_templates"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    applies_to = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(255))

    items = db.relationship(
        "ChecklistItem", backref="template", cascade="all,delete-orphan"
    )


class ChecklistItem(db.Model):
    __tablename__ = "cl_items"

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey("cl_templates.id"), nullable=False)
    section = db.Column(db.String(64), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    critical = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)


class Checklist(db.Model):
    __tablename__ = "checklists"

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey("cl_templates.id"), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipos.id"), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey("operadores.id"))
    date = db.Column(db.Date, default=datetime.utcnow)
    shift = db.Column(db.String(16))
    location = db.Column(db.String(128))
    weather = db.Column(db.String(64))
    hours_start = db.Column(db.Float)
    hours_end = db.Column(db.Float)
    overall_status = db.Column(db.String(16), default="APTO")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    template = db.relationship("ChecklistTemplate")
    equipment = db.relationship("Equipo")
    operator = db.relationship("Operador")
    answers = db.relationship(
        "ChecklistAnswer", backref="checklist", cascade="all,delete-orphan"
    )


class ChecklistAnswer(db.Model):
    __tablename__ = "cl_answers"

    id = db.Column(db.Integer, primary_key=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey("checklists.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("cl_items.id"), nullable=False)
    result = db.Column(
        PGEnum("OK", "FAIL", "NA", name="answerenum", create_type=False),
        nullable=False,
        default="OK",
    )
    note = db.Column(db.String(255))
    photo_path = db.Column(db.String(255))


__all__ = [
    "ChecklistTemplate",
    "ChecklistItem",
    "Checklist",
    "ChecklistAnswer",
    "AnswerEnum",
]
