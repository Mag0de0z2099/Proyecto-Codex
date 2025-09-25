"""Authentication API endpoints."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.auth_service import verify_credentials

bp = Blueprint("auth_api", __name__, url_prefix="/api/v1/auth")


@bp.post("/login")
def login() -> tuple[object, int]:
    """Validate credentials and return a development token."""
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        return jsonify({"detail": "invalid credentials"}), 401

    user = verify_credentials(str(email), str(password))
    if user is None:
        return jsonify({"detail": "invalid credentials"}), 401

    if not getattr(user, "is_approved", False):
        return jsonify({"detail": "not approved"}), 403

    return jsonify({"token": "dev-token"}), 200
