"""Decoradores de autorización reutilizables."""

from __future__ import annotations

from functools import wraps

from flask import current_app
from flask_login import login_required as flask_login_required

try:  # Compatibilidad con decorador existente
    from app.authz import login_required as _legacy_login_required
except Exception:  # pragma: no cover - fallback en caso de import circular
    _legacy_login_required = flask_login_required


def require_login(view_func):
    """Aplica login salvo que ``AUTH_DISABLED`` esté activo."""

    protected_view = _legacy_login_required(view_func)

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if current_app.config.get("AUTH_DISABLED", False):
            return view_func(*args, **kwargs)
        return protected_view(*args, **kwargs)

    return wrapper

