from __future__ import annotations

from app import create_app
from app.db import db
from app.models import User


def ensure_user(username: str, password: str, role: str, title: str | None = None):
    u = User.query.filter_by(username=username).first()
    if not u:
        u = User(username=username, role=role, title=title)
        u.set_password(password)
        if role == "admin":
            u.is_admin = True
        db.session.add(u)
        print(f"Created user: {username} ({role})")
    else:
        print(f"User already exists: {username} ({u.role})")


def main():
    app = create_app()
    with app.app_context():
        ensure_user("admin", "admin", "admin", "Administrador")
        ensure_user("julia", "super123", "supervisor", "Supervisor de obra")
        ensure_user("carlos", "edit123", "editor", "Editor de reportes")
        ensure_user("sofia", "view123", "viewer", "Consulta")

        db.session.commit()
        print("Seed done.")


if __name__ == "__main__":
    main()
