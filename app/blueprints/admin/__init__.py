from __future__ import annotations

from flask import Blueprint

bp_admin = Blueprint("admin", __name__, template_folder="templates")

from . import routes  # noqa: E402,F401
