"""CLI helpers para crear/asegurar un usuario administrador."""

from __future__ import annotations

import click
from flask import current_app

from app.models import User
from app.services.auth_service import ensure_admin_user
from app.utils.strings import normalize_email


def seed_admin_user(
    *, email: str, password: str, username: str | None = None
) -> tuple[User, bool]:
    """Crear o actualizar un administrador y devolver si fue creado."""

    normalized_email = normalize_email(email)
    if not normalized_email:
        raise ValueError("Email inválido")

    existing = (
        User.query.filter_by(email=normalized_email).one_or_none()
        if hasattr(User, "query")
        else None
    )

    user = ensure_admin_user(
        email=normalized_email,
        password=password,
        username=username,
    )

    return user, existing is None


@click.command("seed-admin")
@click.option("--email", required=True, help="Email del administrador a asegurar")
@click.option("--password", required=True, help="Contraseña del administrador")
@click.option(
    "--username",
    required=False,
    help="Username opcional (por defecto se deriva del email)",
)
def seed_admin(email: str, password: str, username: str | None = None) -> None:
    """Crear o actualizar un administrador de forma idempotente."""

    try:
        user, _created = seed_admin_user(
            email=email,
            password=password,
            username=username,
        )
    except ValueError:
        click.echo("Email inválido", err=True)
        raise SystemExit(1)
    except Exception as exc:  # pragma: no cover - registro defensivo
        current_app.logger.exception(
            "No se pudo crear/actualizar el admin", exc_info=exc
        )
        click.echo("No se pudo crear/actualizar el usuario administrador.", err=True)
        raise SystemExit(1)

    click.echo(f"[seed-admin] OK -> {user.email}")


__all__ = ["seed_admin", "seed_admin_user"]
