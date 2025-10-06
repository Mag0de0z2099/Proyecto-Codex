"""Reusable authorization decorators for the Codex app."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from flask import current_app
from flask_login import login_required as flask_login_required

F = TypeVar("F", bound=Callable[..., Any])


def require_login(view_func: F) -> F:
    """Wrap a view with ``flask_login.login_required`` honoring AUTH_DISABLED."""

    login_required_view = flask_login_required(view_func)

    @wraps(view_func)
    def wrapper(*args: Any, **kwargs: Any):
        if (
            current_app.config.get("AUTH_DISABLED")
            or current_app.config.get("LOGIN_DISABLED")
            or current_app.config.get("SECURITY_DISABLED")
        ):
            return view_func(*args, **kwargs)
        return login_required_view(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


__all__ = ["require_login"]
