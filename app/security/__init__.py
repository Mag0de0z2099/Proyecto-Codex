from __future__ import annotations

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from flask import current_app


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


__all__ = ["generate_reset_token", "parse_reset_token", "_serializer"]
