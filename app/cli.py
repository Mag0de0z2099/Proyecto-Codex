"""Comandos personalizados para la CLI de Flask."""

from __future__ import annotations

from datetime import datetime, timezone
from getpass import getpass

import click
from flask import current_app
from werkzeug.security import generate_password_hash

from app.db import db
from app.models import User
from app.services.maintenance_service import cleanup_expired_refresh_tokens
from app.utils.strings import normalize_email


def set_flag(obj, name, value=True):
    if hasattr(obj, name):
        setattr(obj, name, value)


def register_cli(app):
    @app.cli.command("create-admin")
    def create_admin():
        """Crear un usuario administrador de forma interactiva."""

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
    @click.option("--email", required=True, help="Email del administrador a crear")
    @click.option("--password", required=True, help="Contraseña para el administrador")
    def seed_admin(email: str, password: str):
        """Crea o actualiza el usuario admin dejándolo activo y aprobado."""

        normalized_email = normalize_email(email)
        if not normalized_email:
            click.echo("Email inválido", err=True)
            raise SystemExit(1)

        with app.app_context():
            user = User.query.filter_by(email=normalized_email).first()
            if not user:
                user = User(email=normalized_email)
                db.session.add(user)
            else:
                user.email = normalized_email

            if hasattr(user, "username") and not (getattr(user, "username", None) or "").strip():
                user.username = "admin"

            if hasattr(user, "set_password"):
                user.set_password(password)
            elif hasattr(user, "password_hash"):
                user.password_hash = generate_password_hash(password)

            set_flag(user, "role", "admin")
            set_flag(user, "is_admin", True)
            set_flag(user, "is_active", True)
            set_flag(user, "active", True)
            set_flag(user, "approved", True)
            set_flag(user, "is_approved", True)
            set_flag(user, "email_verified", True)
            set_flag(user, "status", "approved")

            if hasattr(user, "approved_at") and getattr(user, "approved_at", None) is None:
                user.approved_at = datetime.now(timezone.utc)
            if hasattr(user, "force_change_password"):
                user.force_change_password = False

            try:
                db.session.commit()
            except Exception as exc:  # pragma: no cover - feedback interactivo
                db.session.rollback()
                current_app.logger.exception(
                    "No se pudo crear/actualizar el admin", exc_info=exc
                )
                click.echo(
                    "No se pudo crear/actualizar el usuario administrador.", err=True
                )
                raise SystemExit(1)

        click.echo(f"Admin listo: {getattr(user, 'username', 'admin')} <{user.email}>")

    @app.cli.command("show-user")
    @click.option("--id", "ident", required=True, help="email o username")
    def show_user(ident: str):
        from sqlalchemy import func, or_

        identifier = (ident or "").strip().lower()
        if not identifier:
            click.echo("No existe el usuario.")
            return

        with app.app_context():
            query = db.session.query(User)
            conditions = [func.lower(User.email) == identifier]

            username_column = getattr(User, "username", None)
            if username_column is not None:
                conditions.append(func.lower(username_column) == identifier)

            if len(conditions) == 1:
                user = query.filter(conditions[0]).first()
            else:
                user = query.filter(or_(*conditions)).first()

            if not user:
                click.echo("No existe el usuario.")
                return

            fields = [
                "id",
                "email",
                "username",
                "role",
                "is_active",
                "active",
                "approved",
                "is_approved",
                "email_verified",
                "status",
            ]

            for field in fields:
                if hasattr(user, field):
                    click.echo(f"{field}: {getattr(user, field)}")

    @app.cli.command("cleanup-refresh")
    @click.option(
        "--grace-days",
        default=0,
        show_default=True,
        help="Días de gracia para conservar refresh expirados.",
    )
    def cleanup_refresh(grace_days: int) -> None:
        """Eliminar refresh tokens expirados y revocados antiguos."""

        result = cleanup_expired_refresh_tokens(grace_days=grace_days)
        click.echo(f"Cleanup done: {result}")

    return app
