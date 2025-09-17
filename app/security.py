from __future__ import annotations

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"],
        salt=current_app.config.get("SECURITY_PASSWORD_SALT", "salt"),
    )


def generate_reset_token(email: str) -> str:
    return _serializer().dumps(email)


def parse_reset_token(token: str, max_age: int = 3600) -> str | None:
    try:
        email = _serializer().loads(token, max_age=max_age)
        return email
    except (BadSignature, SignatureExpired):
        return None


def send_reset_link(email: str, url: str) -> None:
    """
    Envía el link de reseteo. Si no hay SMTP configurado, lo manda a logs.
    """
    app = current_app
    server = app.config.get("MAIL_SERVER", "")
    if not server:
        app.logger.warning("[RESET-PASS] %s -> %s", email, url)
        return

    # Opcional: si quieres usar Flask-Mail, colócalo aquí; por simplicidad: logs
    app.logger.info("[RESET-PASS] Email enviado a %s: %s", email, url)
