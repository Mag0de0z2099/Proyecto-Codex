"""Utility script to make sure an admin user exists locally."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from app import create_app
from app.db import db
from app.models import User
from app.utils.strings import normalize_email


def main() -> None:
    """Create the default admin user if it is missing."""

    app = create_app(os.getenv("CONFIG", "development"))
    username = os.getenv("ADMIN_USERNAME", "admin")
    email = os.getenv("ADMIN_EMAIL", "admin@admin.com")
    password = os.getenv("ADMIN_PASSWORD", "admin123")

    with app.app_context():
        email_n = normalize_email(email)
        if not email_n:
            print("❌ Email inválido; no se crea el admin.")
            return

        user = User.query.filter_by(email=email_n).first()
        resolved_username = (username or email_n.split("@", 1)[0] or "admin").strip()
        candidate = User.query.filter_by(username=resolved_username).first()
        if candidate and not user:
            user = candidate

        created = False
        if not user:
            user = User(
                username=resolved_username,
                email=email_n,
                role="admin",
                is_admin=True,
                is_active=True,
                status="approved",
                approved_at=datetime.now(timezone.utc),
                is_approved=True,
            )
            created = True
            db.session.add(user)

        changed = False

        def _ensure(attr: str, value: object) -> None:
            nonlocal changed
            if getattr(user, attr, None) != value:
                setattr(user, attr, value)
                changed = True

        _ensure("username", resolved_username)
        _ensure("email", email_n)
        _ensure("role", "admin")
        _ensure("is_admin", True)
        _ensure("is_active", True)
        _ensure("status", "approved")
        _ensure("is_approved", True)

        if not getattr(user, "approved_at", None):
            user.approved_at = datetime.now(timezone.utc)
            changed = True

        password_changed = False
        if hasattr(user, "set_password"):
            current_hash = getattr(user, "password_hash", None)
            user.set_password(password)
            password_changed = getattr(user, "password_hash", None) != current_hash
        elif hasattr(user, "password_hash"):
            new_hash = generate_password_hash(password)
            if getattr(user, "password_hash", None) != new_hash:
                user.password_hash = new_hash
                password_changed = True
        else:
            print(
                "❌ El modelo de usuario no soporta asignar contraseña de forma automática."
            )
            return

        try:
            current_flag = getattr(user, "force_change_password", None)
            if current_flag is not None and current_flag is not True:
                user.force_change_password = True
                changed = True
        except Exception:
            pass

        if changed or password_changed or created:
            db.session.commit()

        action = "creado" if created else ("actualizado" if changed or password_changed else "sin cambios")
        if action == "sin cambios":
            print(
                f"ℹ️ Usuario admin ya estaba configurado -> {user.username} / {password}"
                f" (email: {user.email})"
            )
        else:
            print(
                f"✅ Usuario admin {action} -> {user.username} / {password}"
                f" (email: {user.email})"
            )


if __name__ == "__main__":
    main()
