from werkzeug.security import generate_password_hash
from app import create_app
from app.db import db
from app.models import User


def main():
    app = create_app("default")
    with app.app_context():
        if not User.query.filter_by(username="admin").first():
            admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                is_admin=True,
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuario admin creado: admin / admin123")
        else:
            print("⚠️ Usuario admin ya existe")


if __name__ == "__main__":
    main()
