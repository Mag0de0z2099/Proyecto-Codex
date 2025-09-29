from __future__ import annotations

from flask import Blueprint

from app.security import require_login

bp = Blueprint(
    "operadores_bp",
    __name__,
    url_prefix="/operadores",
    template_folder="../../templates/operadores",
)

require_login(bp, exclude=("index",))

from . import routes  # noqa: E402,F401
