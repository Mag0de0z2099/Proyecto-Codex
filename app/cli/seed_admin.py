from __future__ import annotations

from datetime import datetime, timezone

import click
from flask import current_app
from werkzeug.security import generate_password_hash

from app.extensions import db


def _load_user_model():
    try:
        from app.models.user import User  # type: ignore
    except Exception:
        try:
            from app.models import User  # type: ignore
        except Exception as exc:  # pragma: no cover - defensive fallback
            raise RuntimeError("No se pudo importar el modelo User") from exc
    return User


def _assign_username(user_cls, email: str) -> str:
    base = (email.split("@", 1)[0] or email).strip() or "admin"
    candidate = base
    if not hasattr(user_cls, "query"):
        return candidate
    existing = user_cls.query.filter_by(username=candidate).first() if hasattr(user_cls, "username") else None
    if not existing:
        return candidate
    suffix = 1
    while True:
        candidate = f"{base}{suffix}"
        existing = user_cls.query.filter_by(username=candidate).first()
        if not existing:
            return candidate
        suffix += 1


def _set_password(user, password: str) -> None:
    if hasattr(user, "set_password"):
        user.set_password(password)
        return
    hashed = generate_password_hash(password or "")
    if hasattr(user, "password_hash"):
        user.password_hash = hashed
    elif hasattr(user, "password"):
        setattr(user, "password", hashed)


def _update_flags(user) -> None:
    now = datetime.now(timezone.utc)
    for attr, value in (
        ("role", "admin"),
        ("is_admin", True),
        ("is_active", True),
        ("status", "approved"),
        ("is_approved", True),
        ("force_change_password", False),
    ):
        if hasattr(user, attr):
            setattr(user, attr, value)
    if hasattr(user, "approved_at"):
        setattr(user, "approved_at", now)



def register_cli(app) -> None:
    @app.cli.command("users:seed-admin")
    @click.option("--email", default="admin@admin.com", show_default=True)
    @click.option("--password", default="admin123", show_default=True)
    def seed_admin(email: str, password: str) -> None:
        """Crear o actualizar un usuario administrador."""

        email_clean = (email or "").strip().lower()
        if not email_clean:
            click.echo("Email requerido", err=True)
            raise SystemExit(1)

        User = _load_user_model()

        query = getattr(User, "query", None)
        user = None
        if query is not None and hasattr(User, "email"):
            user = query.filter_by(email=email_clean).first()
        elif query is not None and hasattr(User, "username"):
            user = query.filter_by(username=email_clean).first()

        created = False
        if not user:
            user = User()
            created = True
            if hasattr(user, "email"):
                setattr(user, "email", email_clean)
            if hasattr(user, "username"):
                setattr(user, "username", _assign_username(User, email_clean))
            if hasattr(user, "nombre") and not getattr(user, "nombre", None):
                setattr(user, "nombre", "Admin")
            db.session.add(user)

        _set_password(user, password)
        _update_flags(user)

        try:
            db.session.commit()
        except Exception as exc:  # pragma: no cover - defensive logging
            db.session.rollback()
            current_app.logger.exception("No se pudo guardar el admin", exc_info=exc)
            click.echo("No se pudo guardar el usuario administrador.", err=True)
            raise SystemExit(1)

        action = "creado" if created else "actualizado"
        current_app.logger.info("Admin %s: %s", action, email_clean)
        click.echo(f"Admin listo: {email_clean} ({action})")
