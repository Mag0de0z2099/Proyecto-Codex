from flask import Blueprint

bp = Blueprint("checklists", __name__, url_prefix="/checklists")

from . import routes  # noqa: E402,F401
