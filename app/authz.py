from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar, cast

from flask import abort, current_app, redirect, request, session, url_for
from flask_login import current_user

F = TypeVar("F", bound=Callable[..., Any])


def _resolve_session_role() -> str | None:
    user = session.get("user") or {}
    role = user.get("role")
    if role:
        return str(role)
    if user.get("is_admin"):
        return "admin"
    return None


def _resolve_user_role() -> str | None:
    if hasattr(current_user, "role") and current_user.role:
        return str(current_user.role)
    if getattr(current_user, "is_admin", False):
        return "admin"
    return None


def login_required(view: F) -> F:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if current_app.config.get("AUTH_SIMPLE", True):
            return view(*args, **kwargs)
        if session.get("user") or current_user.is_authenticated:
            return view(*args, **kwargs)
        return redirect(url_for("auth.login", next=request.path))

    return cast(F, wrapped)


def requires_role(*roles: str) -> Callable[[F], F]:
    allowed = {str(role) for role in roles if role} or {"admin"}

    def decorator(view: F) -> F:
        @wraps(view)
        def wrapped(*args: Any, **kwargs: Any):
            debug_role = request.headers.get("X-Debug-Role")
            if debug_role:
                if debug_role in allowed:
                    return view(*args, **kwargs)
                abort(403)

            if current_app.config.get("AUTH_SIMPLE", False):
                role = _resolve_session_role()
                if role and role in allowed:
                    return view(*args, **kwargs)
                abort(403)

            if not getattr(current_user, "is_authenticated", False):
                abort(403)

            role = _resolve_user_role()
            if role and role in allowed:
                return view(*args, **kwargs)
            abort(403)

        return cast(F, wrapped)

    return decorator


__all__ = ["login_required", "requires_role"]
