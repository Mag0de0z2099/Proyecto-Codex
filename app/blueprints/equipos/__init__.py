from __future__ import annotations

from flask import Blueprint, current_app

from app.security import require_login

bp = Blueprint("equipos", __name__, url_prefix="/equipos")


@bp.before_request
def _dev_guard():  # type: ignore[func-returns-value]
    if current_app.config.get("SECURITY_DISABLED") or current_app.config.get(
        "LOGIN_DISABLED"
    ):
        return None


require_login(bp, exclude=("index",))

from . import routes  # noqa: E402,F401
