from __future__ import annotations

from datetime import date, datetime, timezone
from random import choice

from app import create_app
from app.db import db
from app.models import (
    Bitacora,
    ChecklistTemplate,
    ChecklistTemplateItem,
    DailyChecklist,
    DailyChecklistItem,
    Project,
    User,
)


def ensure_user(username: str, password: str, role: str, title: str | None = None):
    u = User.query.filter_by(username=username).first()
    if not u:
        u = User(
            username=username,
            role=role,
            title=title,
            status="approved",
            is_active=True,
            approved_at=datetime.now(timezone.utc),
        )
        u.set_password(password)
        if role == "admin":
            u.is_admin = True
        db.session.add(u)
        print(f"Created user: {username} ({role})")
    else:
        print(f"User already exists: {username} ({u.role})")
        u.status = "approved"
        u.is_active = True
        if not u.approved_at:
            u.approved_at = datetime.now(timezone.utc)
        if role == "admin":
            u.is_admin = True


def seed_admin_extra():
    # Proyecto demo si no existe
    project = Project.query.filter_by(name="Huasteca Fuel Terminal").first()
    if not project:
        project = Project(
            name="Huasteca Fuel Terminal",
            client="Gas Natural",
            status="activo",
            progress=42.0,
            budget=3_500_000,
            spent=1_250_000,
        )
        db.session.add(project)
        db.session.commit()

    # Plantilla demo
    template = ChecklistTemplate.query.filter_by(
        name="Checklist diario de dragado"
    ).first()
    if not template:
        template = ChecklistTemplate(name="Checklist diario de dragado", project_id=project.id)
        db.session.add(template)
        db.session.commit()
        base_items = [
            "EPP completo",
            "Señalización en tierra",
            "Control de RP/RSU",
            "Revisión de oleaje/clima",
            "Mantenimiento básico draga",
        ]
        for order, text in enumerate(base_items):
            db.session.add(
                ChecklistTemplateItem(template_id=template.id, text=text, order=order)
            )
        db.session.commit()

    # Checklist del día
    if not DailyChecklist.query.filter_by(
        project_id=project.id, date=date.today()
    ).first():
        checklist = DailyChecklist(
            project_id=project.id,
            date=date.today(),
            created_by="admin",
            status="en_progreso",
        )
        db.session.add(checklist)
        db.session.commit()
        items = (
            ChecklistTemplateItem.query.filter_by(template_id=template.id)
            .order_by(ChecklistTemplateItem.order)
            .all()
        )
        for item in items:
            db.session.add(
                DailyChecklistItem(checklist_id=checklist.id, text=item.text, done=False)
            )
        db.session.commit()

    # Bitácoras de ejemplo
    if not Bitacora.query.first():
        authors = ["sistema", "julia", "carlos"]
        samples = [
            "Inicio de actividades en frente norte. Señalización colocada.",
            "Revisión de oleaje: operación con precaución. Sin incidentes.",
            "Traslado de material dragado al sitio aprobado por SEMARNAT.",
        ]
        for text in samples:
            db.session.add(
                Bitacora(
                    project_id=project.id,
                    author=choice(authors),
                    text=text,
                    date=date.today(),
                )
            )
        db.session.commit()


def main():
    app = create_app()
    with app.app_context():
        ensure_user("admin", "admin", "admin", "Administrador")
        ensure_user("julia", "super123", "supervisor", "Supervisor de obra")
        ensure_user("carlos", "edit123", "editor", "Editor de reportes")
        ensure_user("sofia", "view123", "viewer", "Consulta")

        db.session.commit()
        seed_admin_extra()
        print("Seed demo (usuarios + admin extra) listo.")


if __name__ == "__main__":
    main()
