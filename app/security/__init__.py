"""Security helpers for JWT auth, guards and tokens."""

from __future__ import annotations

from typing import Iterable

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from flask import current_app, redirect, request, url_for
from flask_login import current_user

from .authz import require_login  # noqa: F401
from .guards import requires_auth, requires_role  # noqa: F401
from .jwt import decode_jwt, encode_jwt  # noqa: F401
from .policy import is_locked, register_fail, reset_fail_counter  # noqa: F401

__all__ = [
    "encode_jwt",
    "decode_jwt",
    "requires_auth",
    "requires_role",
    "require_login",
    "register_login_guard",
    "require_login_bp",
    "generate_reset_token",
    "parse_reset_token",
    "is_locked",
    "register_fail",
    "reset_fail_counter",
]


def register_login_guard(bp, exclude: Iterable[str] | None = None) -> None:
    """Apply a login requirement to all routes in a blueprint."""

    exclude_set = set(exclude or ())

    @bp.before_request
    def _guard():  # type: ignore[func-returns-value]
        if current_app.config.get("AUTH_DISABLED") or current_app.config.get(
            "SECURITY_DISABLED"
        ) or current_app.config.get("LOGIN_DISABLED"):
            return None
        endpoint = (request.endpoint or "").split(".")[-1]
        if endpoint in exclude_set:
            return None
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=request.url))

    return None


# Backwards compatibility alias (legacy import path)
require_login_bp = register_login_guard


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"],
        salt=current_app.config.get("SECURITY_PASSWORD_SALT", "dev-salt"),
    )


def generate_reset_token(email: str) -> str:
    return _serializer().dumps(email)


def parse_reset_token(token: str, max_age: int = 3600) -> str | None:
    try:
        return _serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
