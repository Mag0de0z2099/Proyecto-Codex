from __future__ import annotations

import os

from flask import Flask

from app import create_app
from app.db import db
from app.models.user import User


def main() -> None:
    app: Flask = create_app()
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@codex.local").strip().lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin12345")

    with app.app_context():
        u = db.session.query(User).filter_by(email=admin_email).one_or_none()
        if u:
            app.logger.info("[ensure_admin] Admin ya existe: %s", admin_email)
            return

        u = User(email=admin_email, is_admin=True, force_change_password=False)
        u.set_password(admin_password)
        db.session.add(u)
        db.session.commit()
        app.logger.warning("[ensure_admin] Admin creado: %s", admin_email)


if __name__ == "__main__":
    main()
