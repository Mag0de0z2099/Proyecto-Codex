"""Utilities for verifying user credentials used by the auth blueprint."""

from __future__ import annotations

import os
from typing import Any, Mapping

from werkzeug.security import check_password_hash


_DEFAULT_FAKE_USER: Mapping[str, Any] = {
    "id": 1,
    "email": "admin@admin.com",
    "role": "admin",
    "is_admin": True,
    "is_active": True,
}


def _use_fake_backend(app=None) -> bool:
    """Return True when the fake authentication backend should be used."""

    if app is not None and app.config.get("FAKE_AUTH"):
        return True

    raw = os.getenv("FAKE_AUTH", "")
    return str(raw).strip().lower() not in {"", "0", "false", "no", "off"}


def _fake_credentials_match(email: str, password: str) -> bool:
    email = (email or "").strip().lower()
    password = password or ""

    fake_password = os.getenv("FAKE_AUTH_PASSWORD", "admin123")
    return email == _DEFAULT_FAKE_USER["email"] and password == fake_password


def _serialize_user(user: Any, email_fallback: str) -> dict[str, Any]:
    """Build the dictionary representation returned by ``verify_credentials``."""

    email = getattr(user, "email", None) or getattr(user, "username", None) or email_fallback
    role = getattr(user, "role", None)
    if not role:
        role = "admin" if getattr(user, "is_admin", False) else "user"

    return {
        "id": getattr(user, "id", None),
        "email": email,
        "role": role,
        "is_admin": bool(getattr(user, "is_admin", False)),
        "is_active": bool(getattr(user, "is_active", True)),
    }


def _check_user_password(user: Any, password: str) -> bool:
    """Evaluate if the provided password matches the stored credentials."""

    checker = getattr(user, "check_password", None)
    if callable(checker):
        try:
            return bool(checker(password))
        except Exception:
            return False

    stored = getattr(user, "password", None)
    if stored is not None:
        return stored == password

    stored_hash = getattr(user, "password_hash", None)
    if stored_hash:
        try:
            return bool(check_password_hash(stored_hash, password))
        except Exception:
            return False

    return False


def verify_credentials(email: str, password: str, app=None) -> dict[str, Any] | None:
    """Validate the supplied credentials and return a serializable user mapping."""

    email = (email or "").strip().lower()
    password = password or ""

    if _use_fake_backend(app):
        if _fake_credentials_match(email, password):
            return dict(_DEFAULT_FAKE_USER)
        return None

    try:
        from app.db import db
        from app.models import User
    except Exception:
        return None

    try:
        query = db.session.query(User)
        if hasattr(User, "email"):
            query = query.filter_by(email=email)
        elif hasattr(User, "username"):
            query = query.filter_by(username=email)
        user = query.first()
    except Exception:
        return None

    if not user:
        return None

    if hasattr(user, "is_active") and not getattr(user, "is_active"):
        return None

    status = getattr(user, "status", None)
    if status and str(status).lower() not in {"approved", "active", "enabled"}:
        return None

    if not _check_user_password(user, password):
        return None

    return _serialize_user(user, email)


__all__ = ["verify_credentials"]
