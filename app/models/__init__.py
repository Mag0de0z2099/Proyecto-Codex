from __future__ import annotations

from datetime import datetime
from typing import Any

from flask_login import UserMixin
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import db
from app.extensions import bcrypt, login_manager
from app.utils.strings import normalize_email

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
    checklist_templates = db.relationship(
        "ChecklistTemplate", backref="project", lazy=True
    )
    daily_checklists = db.relationship("DailyChecklist", backref="project", lazy=True)


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


# --- MODELOS DE CHECKLISTS ---
class ChecklistTemplate(db.Model):
    __tablename__ = "checklist_templates"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, unique=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=True)
    items = db.relationship(
        "ChecklistTemplateItem", backref="template", cascade="all,delete-orphan"
    )


class ChecklistTemplateItem(db.Model):
    __tablename__ = "checklist_template_items"
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(
        db.Integer, db.ForeignKey("checklist_templates.id"), nullable=False
    )
    text = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer, default=0)


class DailyChecklist(db.Model):
    __tablename__ = "daily_checklists"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    created_by = db.Column(db.String(80))
    status = db.Column(
        db.String(20), default="en_progreso"
    )  # en_progreso / completo
    items = db.relationship(
        "DailyChecklistItem", backref="checklist", cascade="all,delete-orphan"
    )


class DailyChecklistItem(db.Model):
    __tablename__ = "daily_checklist_items"
    id = db.Column(db.Integer, primary_key=True)
    checklist_id = db.Column(
        db.Integer, db.ForeignKey("daily_checklists.id"), nullable=False
    )
    text = db.Column(db.String(255), nullable=False)
    done = db.Column(db.Boolean, default=False)


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


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), unique=False, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="viewer",
        server_default="viewer",
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    title: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    force_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_role", "role"),
        Index("ix_users_status", "status"),
        Index("ix_users_category", "category"),
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password or "")

    def check_password(self, password: str) -> bool:
        stored = self.password_hash or ""
        if stored.startswith("$2"):
            try:
                return bcrypt.check_password_hash(stored, password)
            except Exception:
                pass
        return check_password_hash(stored, password)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "category": self.category,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "title": self.title,
            "is_admin": self.is_admin,
            "force_change_password": self.force_change_password,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() + "Z",
        }

    def can_upload(self) -> bool:
        return self.role in ("admin", "supervisor", "editor")

    def can_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_approved(self) -> bool:
        return (self.status or "").lower() == "approved"

    def __repr__(self) -> str:
        return f"<User {self.username}>"


@event.listens_for(User, "before_insert", propagate=True)
def _user_before_insert(mapper, connection, target):  # pragma: no cover - SQLAlchemy hook
    target.email = normalize_email(target.email)


@event.listens_for(User, "before_update", propagate=True)
def _user_before_update(mapper, connection, target):  # pragma: no cover - SQLAlchemy hook
    target.email = normalize_email(target.email)


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None


from app.models.asset import Asset  # noqa: E402,F401
from app.models.folder import Folder  # noqa: E402,F401


__all__ = [
    "Project",
    "Folder",
    "Asset",
    "Report",
    "Bitacora",
    "MetricDaily",
    "ChecklistTemplate",
    "ChecklistTemplateItem",
    "DailyChecklist",
    "DailyChecklistItem",
    "Todo",
    "User",
]
