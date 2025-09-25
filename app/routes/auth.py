"""Authentication API endpoints."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request, session

from app.services.auth_service import verify_credentials
from app.security.jwt import decode_jwt, encode_jwt, encode_refresh_jwt
from app.security.guards import requires_auth
from app.extensions import limiter

bp = Blueprint("auth_api", __name__, url_prefix="/api/v1/auth")


@bp.post("/login")
@limiter.limit("5 per minute")
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

    role = getattr(user, "role", "user")
    access_token = encode_jwt({"sub": user.id, "email": user.email, "role": role}, ttl_seconds=15 * 60)
    refresh_token = encode_refresh_jwt({"sub": user.id, "email": user.email, "role": role})
    session["token"] = access_token
    return (
        jsonify(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }
        ),
        200,
    )


@bp.get("/me")
@requires_auth
def me() -> tuple[object, int]:
    """Return current user basic information."""
    return jsonify({"email": g.current_user_email, "role": g.current_user_role}), 200


@bp.post("/refresh")
def refresh() -> tuple[object, int]:
    """Issue a new access/refresh pair using a refresh token."""

    auth_header = request.headers.get("Authorization", "")
    body = request.get_json(silent=True) or {}

    token: str | None = None
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        token = body.get("refresh_token")

    if not token:
        return jsonify({"detail": "refresh token required"}), 401

    data = decode_jwt(token) or {}
    if data.get("typ") != "refresh":
        return jsonify({"detail": "invalid refresh"}), 401

    role = data.get("role", "user")
    access_token = encode_jwt(
        {"sub": data.get("sub"), "email": data.get("email"), "role": role},
        ttl_seconds=15 * 60,
    )
    refresh_token = encode_refresh_jwt(
        {"sub": data.get("sub"), "email": data.get("email"), "role": role}
    )
    session["token"] = access_token
    return (
        jsonify(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }
        ),
        200,
    )
