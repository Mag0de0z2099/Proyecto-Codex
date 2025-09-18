from __future__ import annotations

from functools import wraps

from flask import current_app, redirect, request, session, url_for


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_app.config.get("AUTH_SIMPLE", False):
            return view(*args, **kwargs)

        if session.get("user"):
            return view(*args, **kwargs)

        return redirect(url_for("auth.login", next=request.path))

    return wrapped

