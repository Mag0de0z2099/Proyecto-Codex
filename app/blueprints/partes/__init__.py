from __future__ import annotations

from flask import Blueprint

bp = Blueprint("partes", __name__, url_prefix="/partes")

from . import routes  # noqa: E402,F401
