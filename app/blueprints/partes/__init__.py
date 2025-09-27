from __future__ import annotations

from flask import Blueprint

from app.security import require_login

bp = Blueprint("partes", __name__, url_prefix="/partes")

require_login(bp, exclude=("index",))

from . import routes  # noqa: E402,F401
