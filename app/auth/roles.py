from __future__ import annotations

from functools import wraps
from typing import Iterable

from flask import abort, current_app, session
from flask_login import current_user

# Roles disponibles
ROLES: tuple[str, ...] = ("admin", "supervisor", "editor", "viewer")


def _resolve_role_from_session() -> str | None:
    user = session.get("user") or {}
    if not user:
        return None
    role = user.get("role")
    if role:
        return str(role)
    if user.get("is_admin"):
        return "admin"
    return "viewer"


def _resolve_role_from_user() -> str:
    if hasattr(current_user, "role") and current_user.role:
        return str(current_user.role)
    if getattr(current_user, "is_admin", False):
        return "admin"
    return "viewer"


def _normalize_allowed_roles(allowed_roles: Iterable[str]) -> set[str]:
    normalized = {str(role) for role in allowed_roles} or set(ROLES)
    return normalized


def role_required(*allowed_roles: str):
    """Protege una vista: el usuario debe tener uno de los roles permitidos."""

    allowed = _normalize_allowed_roles(allowed_roles)

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if current_app.config.get("SECURITY_DISABLED") or current_app.config.get(
                "LOGIN_DISABLED"
            ):
                return fn(*args, **kwargs)
            if current_app.config.get("AUTH_SIMPLE", False):
                role = _resolve_role_from_session()
                if role is None:
                    abort(401)
                if role not in allowed:
                    abort(403)
                return fn(*args, **kwargs)

            if not current_user.is_authenticated:
                abort(401)
            role = _resolve_role_from_user()
            if role not in allowed:
                abort(403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(fn):
    return role_required("admin")(fn)
