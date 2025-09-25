"""Authentication API endpoints."""

from __future__ import annotations

from flask import Blueprint, jsonify, request, g

from app.services.auth_service import verify_credentials
from app.security.jwt import encode_jwt
from app.security.guards import requires_auth

bp = Blueprint("auth_api", __name__, url_prefix="/api/v1/auth")


@bp.post("/login")
def login() -> tuple[object, int]:
    """Validate credentials and return a JWT token."""
    payload = request.get_json(force=True, silent=True) or {}
    email = payload.get("email")
    password = payload.get("password")

    user = verify_credentials(str(email) if email is not None else None, str(password) if password is not None else None)
    if user is None:
        return jsonify({"detail": "invalid credentials"}), 401

    if not getattr(user, "is_approved", False):
        return jsonify({"detail": "not approved"}), 403

    token = encode_jwt({"sub": user.id, "email": user.email, "role": getattr(user, "role", "user")}, ttl_seconds=3600)
    return jsonify({"access_token": token, "token_type": "bearer"}), 200


@bp.get("/me")
@requires_auth
def me() -> tuple[object, int]:
    """Return current user basic information."""
    return jsonify({"email": g.current_user_email, "role": g.current_user_role}), 200
