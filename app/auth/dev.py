from __future__ import annotations

import os

from flask import Blueprint, current_app, redirect, url_for, abort
from flask_login import login_user

from app.models.user import User


dev_bp = Blueprint("dev_auth", __name__)


@dev_bp.route("/auth/dev-login")
def dev_login():
    env_name = (os.getenv("FLASK_ENV", "production") or "production").lower()
    if env_name.startswith("prod"):
        abort(404)

    user = User.query.filter_by(email="admin@admin.com").first()
    if not user:
        return "No existe admin", 404

    login_user(user, remember=True)

    target = "dashboard.index"
    if target not in current_app.view_functions:
        target = "dashboard_bp.index"
    return redirect(url_for(target))


__all__ = ["dev_bp"]
