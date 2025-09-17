from __future__ import annotations

from flask import Blueprint, redirect, request, url_for
from flask_login import current_user

bp_auth = Blueprint("auth", __name__, template_folder="templates")

@bp_auth.before_app_request
def _enforce_force_change_password():
    allowed = {"auth.logout", "auth.change_password", "static"}
    if (
        current_user.is_authenticated
        and getattr(current_user, "force_change_password", False)
    ):
        endpoint = request.endpoint or ""
        if endpoint not in allowed:
            return redirect(url_for("auth.change_password"))

from . import routes  # noqa: E402,F401
