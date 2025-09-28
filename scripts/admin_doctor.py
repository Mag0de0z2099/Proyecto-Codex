"""Utilidad para normalizar/crear un usuario admin."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Iterable
from pathlib import Path

from sqlalchemy import func

ROOT = Path(__file__).resolve().parents[1]
root_str = os.fspath(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

from app import create_app


def _iter_flags(user: object) -> Iterable[str]:
    """Flags booleanas que intentaremos activar."""

    return (
        flag
        for flag in (
            "is_admin",
            "is_active",
            "active",
            "email_confirmed",
            "confirmed",
            "enabled",
            "is_approved",
        )
        if hasattr(user, flag)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", default="admin@admin.com", help="Email/username destino")
    parser.add_argument("--password", default="admin123", help="Password a configurar")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        from app.extensions import db
        from app.models import User
        from werkzeug.security import check_password_hash, generate_password_hash

        email = args.email
        password = args.password

        lookup_value = email.lower()
        user = None
        if hasattr(User, "email"):
            user = (
                User.query.filter(func.lower(User.email) == lookup_value).first()
            )
        if user is None and hasattr(User, "username"):
            user = (
                User.query.filter(func.lower(User.username) == lookup_value).first()
            )

        created = False
        if user is None:
            kwargs: dict[str, str] = {}
            if hasattr(User, "email"):
                kwargs["email"] = email
            elif hasattr(User, "username"):
                kwargs["username"] = email
            else:
                raise RuntimeError("El modelo User no tiene email ni username")
            user = User(**kwargs)
            db.session.add(user)
            created = True

        # normaliza identificadores
        if hasattr(user, "email"):
            user.email = email
        if hasattr(user, "username"):
            user.username = email

        # activa flags comunes
        for flag in _iter_flags(user):
            setattr(user, flag, True)

        inspector = db.inspect(db.engine)
        columns = {col["name"] for col in inspector.get_columns(getattr(User, "__tablename__", "users"))}
        has_password_hash = "password_hash" in columns
        has_password = "password" in columns

        used_scheme = None
        if hasattr(user, "set_password") and callable(user.set_password):
            user.set_password(password)
            used_scheme = "model.set_password"
        elif hasattr(user, "check_password") and callable(user.check_password):
            # Sin set_password pero con verificador: guardamos hash estándar
            hashed = generate_password_hash(password)
            if has_password_hash and hasattr(user, "password_hash"):
                user.password_hash = hashed
            elif has_password and hasattr(user, "password"):
                user.password = hashed
            else:
                raise RuntimeError("No hay columna compatible para almacenar hash")
            used_scheme = "pbkdf2"
        elif has_password_hash and hasattr(user, "password_hash"):
            user.password_hash = generate_password_hash(password)
            used_scheme = "pbkdf2"
        elif has_password and hasattr(user, "password"):
            user.password = password
            used_scheme = "plain"
        else:
            raise RuntimeError("No se encontró dónde guardar el password")

        db.session.commit()

        # verificación
        verifies = False
        if hasattr(user, "check_password") and callable(user.check_password):
            try:
                verifies = bool(user.check_password(password))
            except Exception:
                verifies = False
        else:
            stored_hash = getattr(user, "password_hash", None)
            stored_plain = getattr(user, "password", None)
            if isinstance(stored_hash, str) and stored_hash:
                try:
                    verifies = check_password_hash(stored_hash, password)
                except Exception:
                    verifies = False
            elif isinstance(stored_plain, str):
                if stored_plain.startswith("pbkdf2:"):
                    try:
                        verifies = check_password_hash(stored_plain, password)
                    except Exception:
                        verifies = False
                else:
                    verifies = stored_plain == password

        preview: dict[str, str | None] = {}
        for attr in ("password_hash", "password"):
            if hasattr(user, attr):
                value = getattr(user, attr)
                if isinstance(value, str) and value:
                    preview[attr] = f"{value[:20]}...(len={len(value)})"
                else:
                    preview[attr] = None

        print("== ADMIN DOCTOR ==")
        print("created:", created)
        print("email:", getattr(user, "email", None))
        print("username:", getattr(user, "username", None))
        for flag in _iter_flags(user):
            print(f"{flag}:", getattr(user, flag))
        print("columns:", sorted(columns))
        print("scheme:", used_scheme)
        print("verifies:", verifies)
        print("preview:", preview)

        if verifies:
            print("READY: intenta login con", email, "/", password)
        else:
            print("NOT READY: revisa la lógica de autenticación")

if __name__ == "__main__":
    main()
