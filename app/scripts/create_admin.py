from app import create_app
from app.db import db
from app.models import User


def main():
    app = create_app()
    with app.app_context():
        u = User.query.filter_by(username="admin").first()
        if not u:
            u = User(username="admin", email=None, is_admin=True, is_active=True)
            u.set_password("admin123")
            db.session.add(u)
            db.session.commit()
            print("Usuario admin creado -> admin / admin123")
        else:
            print("Usuario admin ya existe")


if __name__ == "__main__":
    main()
