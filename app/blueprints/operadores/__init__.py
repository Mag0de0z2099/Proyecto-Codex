from __future__ import annotations

from flask import Blueprint

from app.security import register_login_guard

bp = Blueprint(
    "operadores_bp",
    __name__,
    url_prefix="/operadores",
    template_folder="../../templates/operadores",
)

register_login_guard(bp, exclude=("index",))

from . import routes  # noqa: E402,F401
