"""Health check endpoint for deployment smoke tests."""

from __future__ import annotations

from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.get("/healthz")
def healthz() -> tuple[object, int]:
    """Simple readiness endpoint returning a static payload."""
    return jsonify({"status": "ok"}), 200
