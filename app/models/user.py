from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, Index, Integer, String, event
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import db
from app.extensions import bcrypt
from app.utils.strings import normalize_email


class User(db.Model, UserMixin):
    """Modelo principal de usuarios con helpers de autenticación."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
        server_default="",
    )
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
    failed_logins: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    lock_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        server_default=expression.true(),
    )
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default=expression.false(),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_role", "role"),
        Index("ix_users_status", "status"),
        Index("ix_users_category", "category"),
    )

    def set_password(self, password: str) -> None:
        """Store the password using PBKDF2-SHA256 with a random salt."""

        self.password_hash = generate_password_hash(
            password or "",
            method="pbkdf2:sha256",
            salt_length=16,
        )

    def check_password(self, password: str) -> bool:
        stored = self.password_hash or ""
        if stored.startswith("$2"):
            try:
                return bcrypt.check_password_hash(stored, password)
            except Exception:
                pass
        return check_password_hash(stored, password)

    def approve(self) -> None:
        self.is_approved = True
        if not self.approved_at:
            self.approved_at = datetime.now(timezone.utc)
        try:
            self.status = "approved"
        except Exception:
            self.status = getattr(self, "status", None) or "approved"

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
            "is_approved": self.is_approved,
            "created_at": self.created_at.isoformat() + "Z",
        }

    def can_upload(self) -> bool:
        return self.role in {"admin", "supervisor", "editor"}

    def can_manage_users(self) -> bool:
        return self.role == "admin"

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<User {self.username}>"


def _sync_user_flags(target: User) -> None:
    target.email = normalize_email(target.email)
    status_value = (getattr(target, "status", "") or "").lower()

    if status_value == "approved" and not getattr(target, "is_approved", False):
        target.is_approved = True

    if getattr(target, "is_approved", False):
        if status_value != "approved":
            try:
                target.status = "approved"
            except Exception:
                pass
        if not target.approved_at:
            target.approved_at = datetime.now(timezone.utc)
    else:
        if status_value == "approved":
            try:
                target.status = "pending"
            except Exception:
                pass
        if status_value != "approved":
            target.approved_at = None


@event.listens_for(User, "before_insert", propagate=True)
def _user_before_insert(mapper, connection, target):  # pragma: no cover - SQLAlchemy hook
    _sync_user_flags(target)


@event.listens_for(User, "before_update", propagate=True)
def _user_before_update(mapper, connection, target):  # pragma: no cover - SQLAlchemy hook
    _sync_user_flags(target)


__all__ = ["User"]
