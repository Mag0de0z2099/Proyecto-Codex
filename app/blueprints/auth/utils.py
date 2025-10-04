from __future__ import annotations

from typing import Any

from flask import current_app
from werkzeug.security import check_password_hash


def normalize_email(value: str | None) -> str | None:
    """Normalize email addresses for tolerant comparisons."""

    if not isinstance(value, str):
        return value
    normalized = value.strip().casefold()
    return normalized or None


def _coerce_password_value(stored: str | bytes | None) -> str | None:
    if stored is None:
        return None
    if isinstance(stored, bytes):
        try:
            return stored.decode("utf-8")
        except Exception:
            return None
    if isinstance(stored, str):
        return stored
    return None


def check_pwd_tolerant(stored: str | bytes | None, plain: str) -> bool:
    """Validate *plain* against *stored* supporting multiple hash formats."""

    if not plain:
        return False

    value = _coerce_password_value(stored)
    if not value:
        return False

    try:
        if value.startswith(("pbkdf2:", "scrypt:")) or ":" in value:
            if check_password_hash(value, plain):
                return True
    except Exception:
        # Fall through to other strategies.
        pass

    if value.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            from flask_bcrypt import Bcrypt

            bcrypt = Bcrypt(current_app)
            return bool(bcrypt.check_password_hash(value, plain))
        except Exception:
            return False

    try:
        return bool(check_password_hash(value, plain))
    except Exception:
        return False


def is_active_and_approved(user: Any) -> bool:
    """Return ``True`` if the user appears active/approved across schemas."""

    if hasattr(user, "is_active") and not getattr(user, "is_active"):
        return False

    for flag in ("approved", "is_approved", "aprobado"):
        if hasattr(user, flag) and not getattr(user, flag):
            return False

    for field in ("status", "estado", "state"):
        if hasattr(user, field):
            raw = getattr(user, field)
            value = (raw or "").strip().lower()
            if value in {"rejected", "denied", "pendiente", "pending"}:
                return False

    return True
