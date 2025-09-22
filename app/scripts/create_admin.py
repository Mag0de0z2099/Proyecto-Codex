"""Utility script to make sure an admin user exists locally."""

from __future__ import annotations

import os

from werkzeug.security import generate_password_hash

from app import create_app
from app.db import db
from app.models import User
from app.utils.strings import normalize_email


def main() -> None:
    """Create the default admin user if it is missing."""

    app = create_app(os.getenv("CONFIG", "development"))
    username = os.getenv("ADMIN_USERNAME", "admin")
    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    password = "admin123"

    with app.app_context():
        email_n = normalize_email(email)
        if not email_n:
            print("❌ Email inválido; no se crea el admin.")
            return

        user = User.query.filter_by(email=email_n).first()
        if user:
            print("ℹ️ El usuario admin ya existe; no se cambia la contraseña.")
            return

        resolved_username = (username or email_n.split("@", 1)[0] or "admin").strip()
        if User.query.filter_by(username=resolved_username).first():
            print(
                "ℹ️ Ya existe un usuario con ese username; ajusta ADMIN_USERNAME y reintenta."
            )
            return

        user = User(
            username=resolved_username,
            email=email_n,
            role="admin",
            is_admin=True,
            is_active=True,
        )
        if hasattr(user, "set_password"):
            user.set_password(password)
        elif hasattr(user, "password_hash"):
            user.password_hash = generate_password_hash(password)
        else:
            print(
                "❌ El modelo de usuario no soporta asignar contraseña de forma automática."
            )
            return

        try:
            user.force_change_password = True
        except Exception:
            pass
        db.session.add(user)
        db.session.commit()
        print(
            f"✅ Usuario admin creado -> {resolved_username} / {password}"
            f" (email: {email_n})"
        )


if __name__ == "__main__":
    main()
