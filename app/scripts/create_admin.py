"""Utility script to make sure an admin user exists locally."""

from __future__ import annotations

import os

from werkzeug.security import generate_password_hash

from app import create_app
from app import db
from app.models import User


def main() -> None:
    """Create the default admin user if it is missing."""

    app = create_app(os.getenv("CONFIG", "development"))
    username = os.getenv("ADMIN_USERNAME", "admin")
    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("ADMIN_PASSWORD", "admin123")

    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            print("ℹ️ El usuario admin ya existe")
            return

        user = User(
            username=username,
            email=email,
            role="admin",
            is_admin=True,
            is_active=True,
        )
        user.password_hash = generate_password_hash(password)
        db.session.add(user)
        db.session.commit()
        print(
            f"✅ Usuario admin creado -> {username} / {password}"
            f" (email: {email})"
        )


if __name__ == "__main__":
    main()
