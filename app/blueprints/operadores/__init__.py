from __future__ import annotations

from flask import Blueprint

bp = Blueprint("operadores", __name__, url_prefix="/operadores")

from . import routes  # noqa: E402,F401
