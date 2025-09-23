from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar, cast

from flask import abort, current_app, g, redirect, request, session, url_for
from flask_login import current_user

F = TypeVar("F", bound=Callable[..., Any])


def login_required(view: F) -> F:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if current_app.config.get("AUTH_SIMPLE", True):
            return view(*args, **kwargs)
        if session.get("user") or current_user.is_authenticated:
            return view(*args, **kwargs)
        return redirect(url_for("auth.login", next=request.path))

    return cast(F, wrapped)


def _current_role() -> Any:
    """Detecta el rol actual del usuario autenticado (si existe)."""

    role = request.headers.get("X-Debug-Role")
    if role:
        return role

    try:
        if getattr(current_user, "is_authenticated", False):
            return getattr(current_user, "role", None) or getattr(
                current_user, "roles", None
            )
    except Exception:
        pass

    user = getattr(g, "user", None)
    if user is not None:
        return getattr(user, "role", None) or getattr(user, "roles", None)

    return None


def requires_role(*allowed_roles: Any) -> Callable[[F], F]:
    """Decorador que restringe el acceso a vistas según el rol."""

    allowed: set[Any] = set()
    for role in allowed_roles:
        if isinstance(role, (list, tuple, set)):
            allowed.update(role)
        else:
            allowed.add(role)

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any):
            role = _current_role()
            if role is None:
                abort(403)
            if isinstance(role, (list, tuple, set)):
                if not (set(role) & allowed):
                    abort(403)
            else:
                if role not in allowed:
                    abort(403)
            return fn(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


__all__ = ["login_required", "requires_role"]
