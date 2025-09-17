"""
Script: Crear usuario admin localmente o en Render.
Uso:
  python -m app.scripts.create_admin --username admin --password "TuClave123!"
Variables de entorno opcionales:
  ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL_DOMAIN
"""

from __future__ import annotations

import argparse
import os
from typing import Any

from app import create_app
from app.db import db
from app.models import User  # noqa: F401


def _build_identifiers(username: str) -> tuple[str, str]:
    """Determina el campo y valor a utilizar para buscar al usuario."""

    username = username.strip()
    if not username:
        raise SystemExit("ERROR: El username no puede estar vacío.")

    if hasattr(User, "username"):
        return "username", username

    if hasattr(User, "email"):
        domain = os.getenv("ADMIN_EMAIL_DOMAIN", "codex.local")
        value = username if "@" in username else f"{username}@{domain}"
        return "email", value.lower()

    raise SystemExit("ERROR: El modelo User no expone atributos 'username' ni 'email'.")


def _user_kwargs(username: str) -> dict[str, Any]:
    """Construye los campos necesarios para instanciar o actualizar el usuario."""

    data: dict[str, Any] = {}
    username = username.strip()
    domain = os.getenv("ADMIN_EMAIL_DOMAIN", "codex.local")

    if hasattr(User, "username"):
        data["username"] = username

    if hasattr(User, "email"):
        email_value = username if "@" in username else f"{username}@{domain}"
        data["email"] = email_value.lower()

    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Crear usuario admin")
    parser.add_argument("--username", default=os.getenv("ADMIN_USERNAME", "admin"))
    parser.add_argument("--password", default=os.getenv("ADMIN_PASSWORD"))
    args = parser.parse_args()

    if not args.password:
        raise SystemExit(
            "ERROR: Debes proporcionar --password o la variable ADMIN_PASSWORD."
        )

    field, value = _build_identifiers(args.username)

    app = create_app()
    with app.app_context():
        db.create_all()
        user = User.query.filter_by(**{field: value}).first()
        if user:
            print(f"[INFO] Usuario '{args.username}' ya existe. Actualizando credenciales…")
            user.set_password(args.password)
            if hasattr(user, "is_active"):
                user.is_active = True
            if hasattr(user, "is_admin"):
                user.is_admin = True
            try:
                user.role = "admin"  # type: ignore[attr-defined]
            except Exception:
                pass
            if hasattr(user, "username") and getattr(user, "username", None) != args.username:
                setattr(user, "username", args.username)
            extra = _user_kwargs(args.username)
            for key, val in extra.items():
                setattr(user, key, val)
            if hasattr(user, "force_change_password"):
                setattr(user, "force_change_password", False)
            db.session.commit()
            print("[OK] Admin actualizado.")
            return

        payload = _user_kwargs(args.username)
        if hasattr(User, "is_active"):
            payload.setdefault("is_active", True)
        if hasattr(User, "is_admin"):
            payload.setdefault("is_admin", True)

        user = User(**payload)  # type: ignore[arg-type]

        try:
            user.role = "admin"  # type: ignore[attr-defined]
        except Exception:
            pass

        if hasattr(user, "force_change_password"):
            setattr(user, "force_change_password", False)

        user.set_password(args.password)
        db.session.add(user)
        db.session.commit()
        print(f"[OK] Admin '{args.username}' creado correctamente.")


if __name__ == "__main__":
    main()
