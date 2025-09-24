import os


def _use_fake(app=None) -> bool:
    if app and app.config.get("FAKE_AUTH"):
        return True
    return bool(os.getenv("FAKE_AUTH"))


def verify_credentials(email: str, password: str, app=None):
    """
    Devuelve un dict de usuario si las credenciales son válidas; si no, None.
    En FAKE_AUTH, acepta admin@admin.com / admin123 como demo.
    En modo real intenta consultar la DB si está disponible; si no, None.
    """
    if _use_fake(app):
        if email.lower() == "admin@admin.com" and password == "admin123":
            return {"id": 1, "email": "admin@admin.com", "role": "admin"}
        return None

    try:
        from app.db import db
        from app.models import User
        # ejemplo simple; ajusta a tu hashing real
        user = db.session.query(User).filter(User.email.ilike(email)).first()
        if not user:
            return None
        if hasattr(user, "check_password") and user.check_password(password):
            return {"id": user.id, "email": user.email, "role": getattr(user, "role", "user")}
        # fallback inseguro si no hay hashing; mejor evita en prod
        if getattr(user, "password", None) == password:
            return {"id": user.id, "email": user.email, "role": getattr(user, "role", "user")}
        return None
    except Exception:
        return None
