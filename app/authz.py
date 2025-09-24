from __future__ import annotations

import os
from functools import wraps
from typing import Any, Callable, Iterable, TypeVar, cast

from flask import abort, current_app, g, redirect, request, session, url_for

F = TypeVar("F", bound=Callable[..., Any])


def _resolve_roles(raw: Any) -> set[str]:
    """Normaliza cualquier representación de roles a un conjunto en minúsculas."""

    roles: set[str] = set()
    if raw is None:
        return roles

    if isinstance(raw, str):
        value = raw.strip().lower()
        if value:
            roles.add(value)
        return roles

    if isinstance(raw, Iterable):
        for item in raw:
            roles.update(_resolve_roles(item))
        return roles

    value = str(raw).strip().lower()
    if value:
        roles.add(value)
    return roles


def _current_role():
    """
    Rol actual. El header X-Debug-Role solo se permite en modo testing.
    """
    # Header solo válido en tests
    role = request.headers.get("X-Debug-Role")
    if role and (current_app.config.get("TESTING") or os.getenv("FLASK_ENV") == "testing"):
        return role

    # flask_login (si está instalado)
    try:
        from flask_login import current_user  # type: ignore

        if getattr(current_user, "is_authenticated", False):
            return getattr(current_user, "role", None) or getattr(current_user, "roles", None)
    except Exception:
        pass

    # g.user (objeto o dict)
    user = getattr(g, "user", None)
    if user is not None:
        return getattr(user, "role", None) or getattr(user, "roles", None)

    return None


def _get_current_user() -> Any | None:
    try:
        import flask_login  # type: ignore
    except Exception:
        return None
    return getattr(flask_login, "current_user", None)


def _roles_for_entity(entity: Any) -> set[str]:
    roles = set()
    if entity is None:
        return roles
    has_roles_attr = hasattr(entity, "roles")
    has_role_attr = hasattr(entity, "role")
    if has_roles_attr:
        roles.update(_resolve_roles(getattr(entity, "roles")))
    if has_role_attr:
        roles.update(_resolve_roles(getattr(entity, "role")))
    if not has_roles_attr and not has_role_attr:
        roles.update(_resolve_roles(entity))
    return roles


def login_required(view: F) -> F:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if current_app.config.get("AUTH_SIMPLE", True):
            return view(*args, **kwargs)
        if session.get("user"):
            return view(*args, **kwargs)

        current_user = _get_current_user()
        if current_user is not None and getattr(current_user, "is_authenticated", False):
            return view(*args, **kwargs)
        return redirect(url_for("auth.login", next=request.path))

    return cast(F, wrapped)


def requires_role(*required_roles: str) -> Callable[[F], F]:
    normalized = {role.strip().lower() for role in required_roles if str(role).strip()}

    def decorator(view: F) -> F:
        @wraps(view)
        def wrapped(*args: Any, **kwargs: Any):
            if not normalized:
                return view(*args, **kwargs)

            current_roles = _resolve_roles(_current_role())
            if current_roles & normalized:
                return view(*args, **kwargs)

            user_roles = _roles_for_entity(getattr(g, "user", None))
            if user_roles & normalized:
                return view(*args, **kwargs)

            current_user = _get_current_user()
            if current_user is not None and getattr(current_user, "is_authenticated", False):
                if _roles_for_entity(current_user) & normalized:
                    return view(*args, **kwargs)

            abort(403)

        return cast(F, wrapped)

    return decorator


__all__ = ["login_required", "requires_role"]
