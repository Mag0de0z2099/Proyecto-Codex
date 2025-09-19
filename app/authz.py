from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar, cast

from flask import current_app, redirect, request, session, url_for
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


__all__ = ["login_required"]
