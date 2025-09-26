from __future__ import annotations

from flask import Blueprint

bp = Blueprint("equipos", __name__, url_prefix="/equipos")

from . import routes  # noqa: E402,F401
