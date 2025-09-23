"""Comandos personalizados para la CLI de Flask."""

from __future__ import annotations

from datetime import datetime, timezone
from getpass import getpass

import click
from flask import current_app
from werkzeug.security import generate_password_hash
from app.utils.strings import normalize_email


def register_cli(app):
    @app.cli.command("create-admin")
    def create_admin():
        """Crear un usuario administrador de forma interactiva."""

        from app.db import db
        from app.models import User

        email = input("Email: ").strip()
        password = getpass("Password: ").strip()
        username = input("Username (opcional, se usará el email si se deja vacío): ").strip()

        if not email or not password:
            print("Email y password son obligatorios.")
            return

        email_n = normalize_email(email)
        if not email_n:
            print("Email inválido.")
            return

        if User.query.filter_by(email=email_n).first():
            print("Ya existe un usuario con ese email.")
            return

        if not username:
            username = email_n.split("@", 1)[0]

        if User.query.filter_by(username=username).first():
            print("Ya existe un usuario con ese username.")
            return

        user = User(
            username=username,
            email=email_n,
            role="admin",
            is_admin=True,
            is_active=True,
            status="approved",
            approved_at=datetime.now(timezone.utc),
        )

        if hasattr(user, "set_password"):
            user.set_password(password)
        elif hasattr(user, "password_hash"):
            user.password_hash = generate_password_hash(password)
        else:
            print(
                "El modelo de usuario no soporta asignar contraseña de forma automática."
            )
            return

        if hasattr(user, "force_change_password"):
            user.force_change_password = False

        db.session.add(user)
        try:
            db.session.commit()
        except Exception as exc:  # pragma: no cover - feedback interactivo
            db.session.rollback()
            current_app.logger.exception("No se pudo crear el admin", exc_info=exc)
            print("No se pudo crear el usuario administrador. Revisa los logs.")
            return

        print(f"Admin creado: {user.email} ({user.username})")

    @app.cli.command("seed-admin")
    @click.option("--email", required=True)
    @click.option("--password", required=True)
    @click.option("--role", default="admin")
    def seed_admin(email: str, password: str, role: str) -> None:
        """Crea/actualiza un usuario admin de forma idempotente."""

        try:
            from app.db import db
            from app.models import User
        except Exception as exc:  # pragma: no cover - feedback interactivo
            click.echo(f"[seed-admin] No se pudo importar DB/User: {exc}")
            raise SystemExit(1)

        email_n = normalize_email(email) or (email or "").strip()
        if not email_n:
            click.echo("[seed-admin] Email inválido", err=True)
            raise SystemExit(1)

        with app.app_context():
            user = db.session.query(User).filter_by(email=email_n).one_or_none()
            if user:
                if hasattr(user, "set_password"):
                    user.set_password(password)
                elif hasattr(user, "password_hash"):
                    try:
                        user.password_hash = generate_password_hash(password)
                    except Exception:
                        user.password_hash = password
                elif hasattr(user, "password"):
                    user.password = password

                if hasattr(user, "role"):
                    user.role = role
                if hasattr(user, "is_admin"):
                    user.is_admin = True
                if hasattr(user, "is_active"):
                    user.is_active = True
                if hasattr(user, "status"):
                    try:
                        user.status = "approved"
                    except Exception:
                        pass
                if hasattr(user, "force_change_password"):
                    try:
                        user.force_change_password = False
                    except Exception:
                        pass
                if hasattr(user, "approved_at"):
                    try:
                        user.approved_at = datetime.now(timezone.utc)
                    except Exception:
                        pass
                if hasattr(user, "username") and not getattr(user, "username", None):
                    base_username = email_n.split("@", 1)[0] or "admin"
                    candidate = base_username
                    suffix = 1
                    while db.session.query(User).filter_by(username=candidate).first():
                        suffix += 1
                        candidate = f"{base_username}{suffix}"
                    user.username = candidate

                db.session.commit()
                click.echo(f"[seed-admin] Usuario existente actualizado: {email_n}")
                return

            user = User()
            if hasattr(user, "email"):
                user.email = email_n

            if hasattr(user, "username"):
                base_username = email_n.split("@", 1)[0] or "admin"
                candidate = base_username
                suffix = 1
                while db.session.query(User).filter_by(username=candidate).first():
                    suffix += 1
                    candidate = f"{base_username}{suffix}"
                user.username = candidate

            if hasattr(user, "role"):
                user.role = role
            if hasattr(user, "is_admin"):
                user.is_admin = True
            if hasattr(user, "is_active"):
                user.is_active = True
            if hasattr(user, "status"):
                try:
                    user.status = "approved"
                except Exception:
                    pass
            if hasattr(user, "force_change_password"):
                try:
                    user.force_change_password = False
                except Exception:
                    pass
            if hasattr(user, "approved_at"):
                try:
                    user.approved_at = datetime.now(timezone.utc)
                except Exception:
                    pass

            if hasattr(user, "set_password"):
                user.set_password(password)
            elif hasattr(user, "password_hash"):
                try:
                    user.password_hash = generate_password_hash(password)
                except Exception:
                    user.password_hash = password
            elif hasattr(user, "password"):
                user.password = password

            db.session.add(user)
            db.session.commit()
            click.echo(f"[seed-admin] Usuario creado: {email_n}")

    return app
