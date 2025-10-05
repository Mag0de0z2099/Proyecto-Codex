from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression

from app.db import db
from app.models.user import User

# Import side-effect modules at the end of the file to avoid circular imports.


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False, unique=True)
    client = db.Column(db.String(120), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(40), default="activo")
    progress = db.Column(db.Float, default=0.0)
    budget = db.Column(db.Float, default=0.0)
    spent = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reports = db.relationship("Report", backref="project", lazy=True)
    logs = db.relationship("Bitacora", backref="project", lazy=True)
    metrics = db.relationship("MetricDaily", backref="project", lazy=True)
class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(60), nullable=True)
    date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(40), default="borrador")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Bitacora(db.Model):
    __tablename__ = "bitacoras"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    author = db.Column(db.String(100), nullable=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MetricDaily(db.Model):
    __tablename__ = "metrics_daily"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    kpi_name = db.Column(db.String(80), nullable=False)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Todo(db.Model):
    __tablename__ = "todos"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    completed = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=expression.false(),
    )
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "completed": self.completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }




from app.models.asset import Asset  # noqa: E402,F401
from app.models.checklist import (  # noqa: E402,F401
    ChecklistAnswer,
    ChecklistItem,
    ChecklistRun,
    ChecklistTemplate,
)
from app.models.equipo import Equipo  # noqa: E402,F401
from app.models.folder import Folder  # noqa: E402,F401
from app.models.invite import Invite  # noqa: E402,F401
from app.models.operador import Operador  # noqa: E402,F401
from app.models.parte_diaria import ArchivoAdjunto, ParteDiaria  # noqa: E402,F401
from app.models.refresh_token import RefreshToken  # noqa: E402,F401


__all__ = [
    "Project",
    "Folder",
    "Asset",
    "Report",
    "Bitacora",
    "MetricDaily",
    "ChecklistTemplate",
    "ChecklistItem",
    "ChecklistRun",
    "ChecklistAnswer",
    "Todo",
    "Equipo",
    "Operador",
    "ParteDiaria",
    "ArchivoAdjunto",
    "Invite",
    "RefreshToken",
    "User",
]
