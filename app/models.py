from __future__ import annotations

from datetime import datetime
from typing import Any

from flask_login import UserMixin
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import db
from app.extensions import bcrypt, login_manager


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

    folders = db.relationship("Folder", backref="project", lazy=True)
    reports = db.relationship("Report", backref="project", lazy=True)
    logs = db.relationship("Bitacora", backref="project", lazy=True)
    metrics = db.relationship("MetricDaily", backref="project", lazy=True)


class Folder(db.Model):
    __tablename__ = "folders"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    name = db.Column(db.String(160), nullable=False)
    path = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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
    title: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    force_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_role", "role"),
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

    def __repr__(self) -> str:
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None


__all__ = [
    "Project",
    "Folder",
    "Report",
    "Bitacora",
    "MetricDaily",
    "Todo",
    "User",
]
