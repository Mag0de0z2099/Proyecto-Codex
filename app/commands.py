from __future__ import annotations

import click
from flask import current_app

from app import db
from app.models.user import User


def register_commands(app) -> None:
    """Registra comandos personalizados para la aplicación."""

    @app.cli.command("seed-admin")
    @click.option("--email", required=True)
    @click.option("--password", required=True)
    @click.option("--force", is_flag=True, default=False)
    def seed_admin(email: str, password: str, force: bool) -> None:
        """Crea o actualiza un administrador inicial."""

        email_clean = (email or "").strip().lower()
        if not email_clean:
            raise SystemExit("Email requerido")

        user = User.query.filter_by(email=email_clean).first()
        if user and not force:
            click.echo("Admin ya existe. Usa --force para regenerar la contraseña.")
            return

        if not user:
            user = User(email=email_clean, role="admin", is_active=True)

        user.role = "admin"
        user.is_active = True
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        current_app.logger.info("Admin listo: %s", email_clean)
        click.echo(f"Admin listo: {email_clean}")

    @app.cli.command("set-password")
    @click.option("--email", required=True)
    @click.option("--password", required=True)
    def set_password(email: str, password: str) -> None:
        """Actualiza la contraseña de un usuario existente."""

        email_clean = (email or "").strip().lower()
        if not email_clean:
            raise SystemExit("Email requerido")

        user = User.query.filter_by(email=email_clean).first()
        if not user:
            raise SystemExit("Usuario no encontrado")

        user.set_password(password)
        db.session.commit()
        click.echo("Contraseña actualizada.")
