from flask import Blueprint

from app.security import require_login

bp = Blueprint("checklists", __name__, url_prefix="/checklists")

require_login(bp, exclude=("index",))

from . import routes  # noqa: E402,F401
