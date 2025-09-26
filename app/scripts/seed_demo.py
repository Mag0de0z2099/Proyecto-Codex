from __future__ import annotations

from datetime import date, datetime, timezone
from random import choice

from app import create_app
from app.db import db
from app.models import Bitacora, Project, User


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
