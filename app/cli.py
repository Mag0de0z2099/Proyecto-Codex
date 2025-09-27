"""Comandos personalizados para la CLI de Flask."""

from __future__ import annotations

from datetime import date, datetime, timezone
from getpass import getpass

import click
from flask import current_app
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from app.db import db
from app.models import (
    ActividadDiaria,
    ChecklistItem,
    ChecklistTemplate,
    Equipo,
    Operador,
    ParteDiaria,
    User,
)
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

    email = normalize_email(email)
    if not email:
        click.echo("Email inválido", err=True)
        raise SystemExit(1)

    user = User.query.filter_by(email=email).first()
    if not user:
        base_username = (email.split("@", 1)[0] or "admin").strip() or "admin"
        candidate = base_username
        counter = 1
        while User.query.filter_by(username=candidate).first():
            counter += 1
            candidate = f"{base_username}{counter}"
        user = User(
            email=email,
            username=candidate,
            role="admin",
            is_admin=True,
            is_active=True,
            status="approved",
            is_approved=True,
            approved_at=datetime.now(timezone.utc),
        )
        db.session.add(user)
    else:
        user.role = "admin"
        user.is_admin = True
        user.is_active = True
        if not getattr(user, "approved_at", None):
            user.approved_at = datetime.now(timezone.utc)
        try:
            user.status = "approved"
        except Exception:
            pass
        if hasattr(user, "is_approved"):
            user.is_approved = True

    if hasattr(user, "set_password"):
        user.set_password(password)
    else:
        user.password_hash = generate_password_hash(password)

    db.session.commit()
    click.echo("Admin listo")


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
                "identificacion": "OP-001",
                "puesto": "operador",
                "licencia": "A",
            },
            {
                "nombre": "María López",
                "identificacion": "OP-002",
                "puesto": "ayudante",
                "licencia": "-",
            },
        ]
        for payload in data:
            if not Operador.query.filter_by(identificacion=payload.get("identificacion")).first():
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
            turno="matutino",
            ubicacion="Frente A",
            horas_inicio=1200,
            horas_fin=1208,
            combustible_l=45,
            observaciones="Sin novedades",
        )
        parte.actualizar_horas_trabajadas()
        db.session.add(parte)
        db.session.flush()
        db.session.add(
            ActividadDiaria(
                parte_id=parte.id,
                descripcion="Movimiento de material",
                cantidad=180,
                unidad="m3",
                horas=6.5,
                notas="Zona 1",
            )
        )
        db.session.commit()
        click.echo("Parte demo: OK")

    @app.cli.command("seed-checklist-templates")
    def seed_checklist_templates():
        """Cargar plantillas base de checklists por tipo de equipo."""

        def ensure_template(code: str, name: str, applies_to: str, items: list[tuple[str, str, bool]]):
            template = ChecklistTemplate.query.filter_by(code=code).first()
            if not template:
                template = ChecklistTemplate(code=code, name=name, applies_to=applies_to)
                db.session.add(template)
                db.session.flush()
            else:
                template.name = name
                template.applies_to = applies_to
                db.session.flush()

            ChecklistItem.query.filter_by(template_id=template.id).delete()
            for order, (section, text, critical) in enumerate(items, start=1):
                db.session.add(
                    ChecklistItem(
                        template_id=template.id,
                        section=section,
                        text=text,
                        critical=critical,
                        order=order,
                    )
                )
            db.session.commit()

        exc_items = [
            ("PRE", "Revisión visual general (fugas, daños, pernos)", True),
            ("PRE", "Niveles: motor, hidráulico, refrigerante, combustible", True),
            ("PRE", "Mangueras y racores hidráulicos sin fugas", True),
            ("PRE", "Orugas/llantas: tensión/estado", True),
            ("PRE", "Implemento (cuchara/bucket) y pasadores", True),
            ("PRE", "Alarma de reversa y claxon", True),
            ("PRE", "Luces de trabajo y baliza", False),
            ("PRE", "Limpiaparabrisas, espejo, cámara", False),
            ("PRE", "Extintor vigente y botiquín", True),
            ("PRE", "Cinturón, asiento, E-stop", True),
            ("OP", "Arranque sin ruidos anómalos", True),
            ("OP", "Presión hidráulica/temperatura en rango", True),
            ("OP", "Rotación torre sin vibración excesiva", False),
            ("OP", "Freno/retención y bloqueo implemento", True),
            ("OP", "Instrumentos y panel sin alertas", True),
            ("OP", "Radio/comunicación operativa", False),
            ("POST", "Limpieza cabina/implemento, retiro residuos", False),
            ("POST", "Registro de horas y combustible", False),
            ("POST", "Reporte de fallas y fotos adjuntas si aplica", True),
            ("POST", "Estacionamiento seguro, pluma apoyada", True),
        ]
        ensure_template(
            "CL-EXC",
            "Excavadora — Diario",
            "excavadora|excavadora hidráulica",
            exc_items,
        )

        drg_items = [
            ("PRE", "Inspección casco/pontones y estanqueidad", True),
            ("PRE", "Sistema de espigas (spuds) y gatos", True),
            ("PRE", "Winches de swing y cables/guayas", True),
            ("PRE", "Bomba de dragado: sello, acople, carcasa", True),
            ("PRE", "Cabezales (cutter/suction) integridad", True),
            ("PRE", "Tubería de descarga y juntas/liners", True),
            ("PRE", "Motor principal y auxiliares (niveles/ correas)", True),
            ("PRE", "Sistema eléctrico y tableros; E-stop", True),
            ("PRE", "Navegación/luminarias, bocina, radio", True),
            ("PRE", "Kit anticontaminación (barreras/absorbentes)", True),
            ("OP", "Presión/caudal bomba dentro de rango", True),
            ("OP", "Temperaturas motor/caja reductora normales", True),
            ("OP", "Vibración anormal en cutter o bomba", True),
            ("OP", "Anclajes y spuds operando correctamente", True),
            ("OP", "Monitoreo de presión en línea de descarga", True),
            ("POST", "Purgado/limpieza bomba y línea", True),
            ("POST", "Bitácora de horas, producción y consumo", False),
            ("POST", "Reporte de fugas/incidencias con fotos", True),
            ("POST", "Asegurar equipos, cortar energía, verificar flotabilidad", True),
        ]
        ensure_template(
            "CL-DRG",
            "Draga — Diario",
            "draga|cortador|draga succión",
            drg_items,
        )

        vol_items = [
            ("PRE", "Llantas (presión/desgaste) y tuercas", True),
            ("PRE", "Frenos y nivel de aire", True),
            ("PRE", "Dirección y suspensión (fugas/bujes)", True),
            ("PRE", "Luces, direccionales, baliza y claxon", True),
            ("PRE", "Volteo: cilindro, mangueras, pasadores", True),
            ("PRE", "Extintor/triángulos/botiquín", True),
            ("OP", "Tablero sin testigos críticos", True),
            ("OP", "Freno de servicio/estacionamiento", True),
            ("OP", "Subida/bajada de caja sin golpes", True),
            ("POST", "Lavado de chasis, retiro de material", False),
            ("POST", "Registro de km/horas y consumo", False),
            ("POST", "Reporte de daños/incidentes con fotos", True),
        ]
        ensure_template(
            "CL-VOL",
            "Camión de Volteo — Diario",
            "volteo|camión|camion",
            vol_items,
        )

        click.echo("Plantillas de checklist: OK")

    return app
