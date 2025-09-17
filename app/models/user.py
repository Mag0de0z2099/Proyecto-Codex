from __future__ import annotations

from datetime import datetime
from typing import Any

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import db
from app.extensions import bcrypt, login_manager


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), unique=False, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    force_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("ix_users_username", "username"),)

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
            "is_admin": self.is_admin,
            "force_change_password": self.force_change_password,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() + "Z",
        }

    def __repr__(self) -> str:
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None
