"""Decoradores simples para control de acceso basado en roles/aprobación."""

from __future__ import annotations

from functools import wraps

from flask import abort, current_app, session
from flask_login import current_user


def _resolve_session_role() -> str | None:
    user = session.get("user") or {}
    role = user.get("role")
    if role:
        return str(role)
    if user.get("is_admin"):
        return "admin"
    return None


def require_roles(*roles: str):
    """Permite el acceso solo a usuarios autenticados con alguno de los roles."""

    allowed = {str(role) for role in roles if role}

    def deco(fn):
        @wraps(fn)
        def wrap(*a, **k):
            if current_app.config.get("SECURITY_DISABLED") or current_app.config.get(
                "LOGIN_DISABLED"
            ):
                return fn(*a, **k)
            if current_app.config.get("AUTH_SIMPLE", False):
                role = _resolve_session_role()
                if role is None:
                    abort(401)
                if allowed and role not in allowed:
                    abort(403)
                return fn(*a, **k)

            if not getattr(current_user, "is_authenticated", False):
                abort(401)
            role = getattr(current_user, "role", None)
            if role is None and getattr(current_user, "is_admin", False):
                role = "admin"
            if allowed and role not in allowed:
                abort(403)
            return fn(*a, **k)

        return wrap

    return deco


def require_approved(fn):
    """Bloquea acceso a usuarios no aprobados."""

    @wraps(fn)
    def wrap(*a, **k):
        if current_app.config.get("SECURITY_DISABLED") or current_app.config.get(
            "LOGIN_DISABLED"
        ):
            return fn(*a, **k)
        if current_app.config.get("AUTH_SIMPLE", False):
            if not session.get("user"):
                abort(401)
            return fn(*a, **k)

        if not getattr(current_user, "is_authenticated", False):
            abort(401)
        if not getattr(current_user, "is_approved", False):
            abort(403)
        return fn(*a, **k)

    return wrap
