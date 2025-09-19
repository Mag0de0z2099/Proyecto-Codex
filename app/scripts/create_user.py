import os

from app import create_app
from app.db import db
from app.models import User


def main():
    app = create_app()

    username = os.environ.get("ADMIN_USER", "admin")
    password = os.environ.get("ADMIN_PASS", "1234")
    email = os.environ.get("ADMIN_EMAIL")  # opcional

    with app.app_context():
        user = User.query.filter_by(username=username).first()

        if user:
            # Actualizar contraseña existente
            user.set_password(password)
            if email:
                user.email = email
            user.is_admin = True
            user.role = "admin"
            db.session.commit()
            print(f"[OK] Usuario '{username}' ya existía. Contraseña actualizada.")
        else:
            # Crear usuario nuevo
            u = User(
                username=username,
                email=email,
                role="admin",
                is_admin=True,
                is_active=True,
            )
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            print(f"[OK] Usuario '{username}' creado con contraseña '{password}'")


if __name__ == "__main__":
    main()
