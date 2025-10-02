"""Comandos personalizados para la CLI de Flask."""

from __future__ import annotations

from datetime import date, datetime, timezone
from getpass import getpass

import click
from flask import current_app
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from .seed_admin import register_cli as register_seed_admin_cli

from app.db import db
from app.models import ChecklistItem, ChecklistTemplate, Equipo, Operador, ParteDiaria, User
from app.services.auth_service import ensure_admin_user
from app.services.maintenance_service import cleanup_expired_refresh_tokens
from app.utils.strings import normalize_email


@click.group()
def users():
    """Comandos relacionados con usuarios."""


@users.command("ensure-admin")
@click.option("--email", required=True)
@click.option("--password", required=True)
@with_appcontext
def ensure_admin(email: str, password: str) -> None:
    """Crear o actualizar un administrador con las credenciales dadas."""

    try:
        user = ensure_admin_user(email=email, password=password)
    except ValueError:
        click.echo("Email inválido", err=True)
        raise SystemExit(1)

    click.echo(f"Admin listo: {user.email}")


def register_cli(app):
    app.cli.add_command(users)

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
    @click.option(
        "--password",
        required=False,
        default="admin123",
        show_default=True,
        help="Contraseña para el administrador (no se muestra en logs)",
    )
    @click.option(
        "--username",
        required=False,
        help="Username opcional (por defecto se deriva del email)",
    )
    def seed_admin(email: str, password: str, username: str | None = None):
        """Crear o actualizar un administrador de forma no interactiva."""

        resolved_password = password or "admin123"
        try:
            user = ensure_admin_user(email=email, password=resolved_password, username=username)
        except ValueError:
            click.echo("Email inválido", err=True)
            raise SystemExit(1)
        except Exception as exc:  # pragma: no cover - feedback interactivo
            current_app.logger.exception("No se pudo crear/actualizar el admin", exc_info=exc)
            click.echo("No se pudo crear/actualizar el usuario administrador.", err=True)
            raise SystemExit(1)

        click.echo(f"✅ Admin listo: {user.email} ({user.username})")

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

    @app.cli.command("seed-equipos")
    def seed_equipos():
        """Cargar equipos de demostración si no existen."""

        data = [
            {"codigo": "EXC-001", "tipo": "excavadora", "marca": "CAT", "modelo": "320D", "status": "activo"},
            {"codigo": "DRG-028", "tipo": "draga", "marca": "IHC", "modelo": "28m", "status": "mantenimiento"},
        ]
        for payload in data:
            if not Equipo.query.filter_by(codigo=payload["codigo"]).first():
                db.session.add(Equipo(**payload))
        db.session.commit()
        click.echo("Equipos seed: OK")

    @app.cli.command("seed-operadores")
    def seed_operadores():
        """Cargar operadores de demostración si no existen."""

        data = [
            {
                "nombre": "Juan Pérez",
                "doc_id": "LIC-001",
                "licencia_vence": date.today(),
                "notas": "Operador principal de excavadora.",
                "estatus": "activo",
            },
            {
                "nombre": "María López",
                "doc_id": "LIC-002",
                "licencia_vence": date.today(),
                "notas": "Respaldo turno nocturno.",
                "estatus": "activo",
            },
        ]
        for payload in data:
            if not Operador.query.filter_by(doc_id=payload.get("doc_id")).first():
                db.session.add(Operador(**payload))
        db.session.commit()
        click.echo("Operadores seed: OK")

    @app.cli.command("seed-partes-demo")
    def seed_partes_demo():
        """Crear un parte diario de demostración vinculado al primer equipo disponible."""

        equipo = Equipo.query.first()
        if not equipo:
            click.echo("Primero crea o carga equipos.")
            return

        parte = ParteDiaria(
            fecha=date.today(),
            equipo_id=equipo.id,
            horas_trabajo=6.5,
            actividad="Movimiento de material",
            incidencias="",
            notas="Sin novedades",
        )
        db.session.add(parte)
        db.session.commit()
        click.echo("Parte demo: OK")

    @app.cli.command("seed-checklist-templates")
    def seed_checklist_templates():
        """Cargar plantillas base de checklists por tipo de equipo."""

        samples = [
            {
                "nombre": "Excavadora — Diario",
                "norma": "NOM-017-STPS",
                "items": [
                    "Revisión visual general",
                    "Niveles del motor e hidráulicos",
                    "Luces y alarma de reversa",
                    "Extintor y botiquín en sitio",
                    "Registro de horas",
                ],
            },
            {
                "nombre": "Draga — Inicio de jornada",
                "norma": "NOM-002-STPS",
                "items": [
                    "Spuds operativos",
                    "Bomba sin fugas",
                    "Presión de descarga",
                    "Kit anticontaminación",
                    "Bitácora actualizada",
                ],
            },
        ]

        for tpl in samples:
            template = ChecklistTemplate.query.filter_by(nombre=tpl["nombre"]).first()
            if not template:
                template = ChecklistTemplate(nombre=tpl["nombre"], norma=tpl.get("norma"))
                db.session.add(template)
                db.session.flush()
            else:
                template.norma = tpl.get("norma")
                db.session.flush()

            ChecklistItem.query.filter_by(template_id=template.id).delete()
            for order, texto in enumerate(tpl["items"], start=1):
                db.session.add(
                    ChecklistItem(
                        template_id=template.id,
                        texto=texto,
                        tipo="bool",
                        orden=order,
                    )
        )
        db.session.commit()
        click.echo("Plantillas de checklist: OK")

    register_seed_admin_cli(app)

    return app
