from __future__ import annotations

import os

from flask import Blueprint, jsonify

bp = Blueprint("version", __name__, url_prefix="/api")


@bp.get("/version")
def version():
    return (
        jsonify(
            version=os.getenv("APP_VERSION", "dev"),
            commit=os.getenv("GIT_SHA", "local"),
            env=os.getenv("FLASK_ENV")
            or os.getenv("ENV")
            or "production",
        ),
        200,
    )
