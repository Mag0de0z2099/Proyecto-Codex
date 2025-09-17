from werkzeug.security import generate_password_hash
from app import create_app
from app.db import db
from app.models import User


def main():
    app = create_app("default")
    with app.app_context():
        # idempotente: solo lo crea si no existe
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                is_admin=True,
                is_active=True,
                # obligar a cambiar la contraseña en el primer inicio de sesión
                force_change_password=True,
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuario admin creado: admin / admin123 (cambio obligatorio)")
        else:
            if getattr(admin, "force_change_password", None) is None:
                admin.force_change_password = True
                db.session.commit()
            print("ℹ️ Usuario admin ya existe")


if __name__ == "__main__":
    main()
