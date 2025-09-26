from __future__ import annotations

from flask import Blueprint

bp = Blueprint("dashboard", __name__, url_prefix="")

from . import routes  # noqa: E402,F401
