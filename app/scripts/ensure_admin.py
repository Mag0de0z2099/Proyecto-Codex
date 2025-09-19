from __future__ import annotations

import os

from flask import Flask

from app import create_app
from app.db import db
from app.models import User


def main() -> None:
    app: Flask = create_app()
    username = os.environ.get("ADMIN_USERNAME", "admin")
    password = os.environ.get("ADMIN_PASSWORD", "admin")

    with app.app_context():
        u = User.query.filter_by(username=username).first()
        if u:
            app.logger.info("[ensure_admin] ya existe '%s'", username)
            return

        u = User(
            username=username,
            email=None,
            role="admin",
            is_admin=True,
            is_active=True,
            force_change_password=False,
        )
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        app.logger.warning(
            "[ensure_admin] creado admin '%s' con password '%s'",
            username,
            password,
        )


if __name__ == "__main__":
    main()
