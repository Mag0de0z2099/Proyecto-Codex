from app import create_app

def main():
    app = create_app()
    with app.app_context():
        from app.extensions import db
        from app.models import User
        from werkzeug.security import generate_password_hash

        EMAIL = "admin@admin.com"
        PASS = "admin123"

        # busca por email o username
        u = None
        if hasattr(User, "email"):
            u = User.query.filter_by(email=EMAIL).first()
        if not u and hasattr(User, "username"):
            u = User.query.filter_by(username=EMAIL).first()

        if not u:
            kwargs = {}
            if hasattr(User, "email"):
                kwargs["email"] = EMAIL
            elif hasattr(User, "username"):
                kwargs["username"] = EMAIL
            u = User(**kwargs)
            db.session.add(u)

        # flags
        if hasattr(u, "is_admin"):
            u.is_admin = True
        if hasattr(u, "is_active"):
            u.is_active = True
        if hasattr(u, "username") and not getattr(u, "username", None):
            u.username = EMAIL

        # password (password_hash o password)
        h = generate_password_hash(PASS)
        if hasattr(u, "set_password"):
            u.set_password(PASS)
        else:
            if hasattr(u, "password_hash"):
                u.password_hash = h
            elif hasattr(u, "password"):
                u.password = h
            else:
                raise RuntimeError("User no tiene password_hash/password")

        db.session.commit()
        print("OK: admin asegurado")

if __name__ == "__main__":
    main()
