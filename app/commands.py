"""Registro perezoso de comandos CLI."""

from __future__ import annotations

from datetime import datetime, timezone

import click

from app.extensions import db
from app.models import User


def _assign_username(email: str) -> str:
    base = (email.split("@", 1)[0] or email or "admin").strip() or "admin"
    if not hasattr(User, "query") or not hasattr(User, "username"):
        return base

    candidate = base
    suffix = 1
    while User.query.filter_by(username=candidate).first():
        candidate = f"{base}{suffix}"
        suffix += 1
    return candidate


def register_commands(app):
    """Registrar los comandos CLI principales evitando ciclos tempranos."""

    from .cli import register_cli
    from .cli_sync import register_sync_cli

    register_cli(app)
    register_sync_cli(app)

    if "seed-admin" not in app.cli.commands:

        @app.cli.command("seed-admin")
        @click.option("--email", required=True)
        @click.option("--password", required=True)
        @click.option("--force", is_flag=True, default=False)
        def seed_admin(email: str, password: str, force: bool) -> None:
            """Crear o actualizar un usuario administrador con contraseña segura."""

            email_clean = (email or "").strip().lower()
            if not email_clean:
                click.echo("Email requerido", err=True)
                raise SystemExit(1)

            user = User.query.filter_by(email=email_clean).first() if hasattr(User, "email") else None
            if user and not force:
                click.echo("Admin ya existe. Usa --force para regenerar la contraseña.")
                return

            if not user:
                user = User()
                if hasattr(user, "email"):
                    setattr(user, "email", email_clean)
                if hasattr(user, "username"):
                    setattr(user, "username", _assign_username(email_clean))
                db.session.add(user)

            if hasattr(user, "set_password"):
                user.set_password(password)
            elif hasattr(user, "password_hash"):
                from werkzeug.security import generate_password_hash

                user.password_hash = generate_password_hash(password or "")

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
                setattr(user, "approved_at", datetime.now(timezone.utc))

            db.session.commit()
            click.echo(f"Admin listo: {email_clean}")

    @app.cli.command("set-password")
    @click.option("--email", required=True)
    @click.option("--password", required=True)
    def set_password(email: str, password: str) -> None:
        """Actualizar la contraseña de un usuario existente."""

        email_clean = (email or "").strip().lower()
        if not email_clean:
            raise SystemExit("Usuario no encontrado")

        user = User.query.filter_by(email=email_clean).first() if hasattr(User, "email") else None
        if not user:
            raise SystemExit("Usuario no encontrado")

        if hasattr(user, "set_password"):
            user.set_password(password)
        elif hasattr(user, "password_hash"):
            from werkzeug.security import generate_password_hash

            user.password_hash = generate_password_hash(password or "")

        db.session.commit()
        click.echo("Contraseña actualizada.")
