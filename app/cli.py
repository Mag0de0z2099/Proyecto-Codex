"""Comandos personalizados para la CLI de Flask."""

from __future__ import annotations

from getpass import getpass

import click
from flask import current_app
from werkzeug.security import generate_password_hash

from app import db
from app.models import User
from app.utils.strings import normalize_email


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
    @click.option(
        "--password",
        required=True,
        help="Contraseña para el administrador (no se muestra en logs)",
    )
    @click.option(
        "--username",
        required=False,
        help="Username opcional (por defecto se deriva del email)",
    )
    def seed_admin(email: str, password: str, username: str | None = None):
        """Crear o asegurar la existencia de un admin de forma no interactiva."""

        email_n = normalize_email(email)
        if not email_n:
            click.echo("Email inválido", err=True)
            raise SystemExit(1)

        if User.query.filter_by(email=email_n).first():
            click.echo("Ya existe un usuario con ese email, nada por hacer.")
            return

        resolved_username = (username or email_n.split("@", 1)[0] or "admin").strip()
        if User.query.filter_by(username=resolved_username).first():
            click.echo(
                "Ya existe un usuario con ese username; especifica otro con --username.",
                err=True,
            )
            raise SystemExit(1)

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
            click.echo(
                "El modelo de usuario no soporta asignar contraseña de forma automática.",
                err=True,
            )
            raise SystemExit(1)

        if hasattr(user, "force_change_password"):
            user.force_change_password = False

        db.session.add(user)
        try:
            db.session.commit()
        except Exception as exc:  # pragma: no cover - feedback interactivo
            db.session.rollback()
            current_app.logger.exception("No se pudo crear el admin", exc_info=exc)
            click.echo("No se pudo crear el usuario administrador. Revisa los logs.", err=True)
            raise SystemExit(1)

        click.echo(f"Admin creado: {user.email} ({user.username})")

    return app
