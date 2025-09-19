from __future__ import annotations

from sqlalchemy import inspect
from werkzeug.security import generate_password_hash

from app import create_app
from app.db import db
from app.models import User


def main() -> None:
    app = create_app()
    with app.app_context():
        insp = inspect(db.engine)
        if not insp.has_table("users"):
            db.create_all()

        if not User.query.filter_by(username="admin").first():
            user = User(
                username="admin",
                email=None,
                password_hash=generate_password_hash("admin"),
                is_admin=True,
                is_active=True,
                force_change_password=False,
            )
            db.session.add(user)
            db.session.commit()
            print("Admin creado: admin / admin")


if __name__ == "__main__":
    main()
