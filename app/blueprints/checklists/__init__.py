from flask import Blueprint, current_app

from app.security import require_login

bp = Blueprint("checklists", __name__, url_prefix="/checklists")


@bp.before_request
def _dev_guard():  # type: ignore[func-returns-value]
    if current_app.config.get("SECURITY_DISABLED") or current_app.config.get(
        "LOGIN_DISABLED"
    ):
        return None


require_login(bp, exclude=("index",))

from . import routes  # noqa: E402,F401
