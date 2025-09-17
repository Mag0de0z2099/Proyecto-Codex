from app import create_app
from app.db import db
from app.models.user import User


def main():
    app = create_app()
    with app.app_context():
        username = "admin"
        password = "1234"  # cámbialo cuando entres
        email = None

        existing = User.query.filter_by(username=username).first()
        if existing:
            print(f"El usuario '{username}' ya existe")
            return

        u = User(username=username, email=email, is_admin=True, is_active=True)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        print(f"Usuario '{username}' creado con contraseña '{password}'")


if __name__ == "__main__":
    main()
