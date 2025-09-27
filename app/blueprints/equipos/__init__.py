from __future__ import annotations

from flask import Blueprint

from app.security import require_login

bp = Blueprint("equipos", __name__, url_prefix="/equipos")

require_login(bp, exclude=("index",))

from . import routes  # noqa: E402,F401
