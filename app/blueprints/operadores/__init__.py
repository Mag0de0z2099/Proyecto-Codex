from __future__ import annotations

from flask import Blueprint

from app.security import require_login

bp = Blueprint("operadores", __name__, url_prefix="/operadores")

require_login(bp, exclude=("index",))

from . import routes  # noqa: E402,F401
