"""Authentication API endpoints."""

from __future__ import annotations

import logging

from flask import Blueprint, g, jsonify, request, session

from app.extensions import limiter, user_or_ip
from app.security.guards import requires_auth
from app.security.jwt import decode_jwt, encode_jwt, encode_refresh_jwt, gen_jti
from app.services.auth_service import verify_credentials
from app.services.token_service import (
    create_refresh_record,
    is_active,
    revoke_all_for_user,
    revoke_jti,
)

bp = Blueprint("auth_api", __name__, url_prefix="/api/v1/auth")

log = logging.getLogger("auth")


@bp.post("/login")
@limiter.limit("5 per minute")
def login() -> tuple[object, int]:
    """Validate credentials and return a JWT token."""

    payload = request.get_json(force=True, silent=True) or {}
    email = payload.get("email")
    password = payload.get("password")

    user = verify_credentials(
        str(email) if email is not None else None,
        str(password) if password is not None else None,
    )
    if user is None:
        log.warning(
            "login failed",
            extra={"event": "login_failed", "email": email, "status": 401},
        )
        return jsonify({"detail": "invalid credentials"}), 401

    if not getattr(user, "is_approved", False):
        log.warning(
            "login not approved",
            extra={
                "event": "login_not_approved",
                "user_id": None,
                "email": email,
                "status": 403,
            },
        )
        return jsonify({"detail": "not approved"}), 403

    role = getattr(user, "role", "user")
    access_token = encode_jwt(
        {"sub": user.id, "email": user.email, "role": role}, ttl_seconds=15 * 60
    )
    refresh_jti = gen_jti()
    refresh_token = encode_refresh_jwt(
        {"sub": user.id, "email": user.email, "role": role}, jti=refresh_jti
    )
    create_refresh_record(user_id=user.id, jti=refresh_jti)
    log.info(
        "login ok",
        extra={
            "event": "login_ok",
            "user_id": user.id,
            "email": user.email,
            "status": 200,
        },
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


@bp.get("/me")
@requires_auth
@limiter.limit("120 per minute", key_func=user_or_ip)
def me() -> tuple[object, int]:
    """Return current user basic information."""

    return jsonify({"email": g.current_user_email, "role": g.current_user_role}), 200


@bp.post("/refresh")
@limiter.limit("20 per minute", key_func=user_or_ip)
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
        log.warning(
            "refresh missing token",
            extra={"event": "refresh_missing_token", "status": 401},
        )
        return jsonify({"detail": "refresh token required"}), 401

    data = decode_jwt(token) or {}
    if data.get("typ") != "refresh":
        log.warning(
            "refresh invalid",
            extra={"event": "refresh_invalid", "status": 401},
        )
        return jsonify({"detail": "invalid refresh"}), 401

    sub = data.get("sub")
    old_jti = data.get("jti")
    try:
        sub_int = int(sub)
    except (TypeError, ValueError):
        log.warning(
            "refresh invalid",
            extra={"event": "refresh_invalid", "status": 401},
        )
        return jsonify({"detail": "invalid refresh"}), 401

    if not old_jti:
        log.warning(
            "refresh invalid",
            extra={"event": "refresh_invalid", "status": 401},
        )
        return jsonify({"detail": "invalid refresh"}), 401

    if not is_active(old_jti, user_id=sub_int):
        log.warning(
            "refresh revoked or expired",
            extra={
                "event": "refresh_revoked_or_expired",
                "user_id": sub_int,
                "status": 401,
            },
        )
        return jsonify({"detail": "refresh revoked or expired"}), 401

    revoke_jti(old_jti)

    role = data.get("role", "user")
    access_token = encode_jwt(
        {"sub": sub_int, "email": data.get("email"), "role": role}, ttl_seconds=15 * 60
    )
    new_jti = gen_jti()
    refresh_token = encode_refresh_jwt(
        {"sub": sub_int, "email": data.get("email"), "role": role}, jti=new_jti
    )
    create_refresh_record(user_id=sub_int, jti=new_jti)
    log.info(
        "refresh ok",
        extra={"event": "refresh_ok", "user_id": sub_int, "status": 200},
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


@bp.post("/logout")
@limiter.limit("30 per minute", key_func=user_or_ip)
def logout() -> tuple[object, int]:
    """Revoke a specific refresh token."""

    auth_header = request.headers.get("Authorization", "")
    body = request.get_json(silent=True) or {}

    token: str | None = None
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        token = body.get("refresh_token")

    if not token:
        log.warning(
            "logout missing token",
            extra={"event": "logout_missing_token", "status": 400},
        )
        return jsonify({"detail": "refresh token required"}), 400

    data = decode_jwt(token) or {}
    if data.get("typ") != "refresh" or "jti" not in data:
        log.warning(
            "logout invalid refresh",
            extra={"event": "logout_invalid_refresh", "status": 401},
        )
        return jsonify({"detail": "invalid refresh"}), 401

    revoke_jti(str(data["jti"]))
    session.pop("token", None)
    log.info("logout ok", extra={"event": "logout_ok", "status": 200})
    return jsonify({"detail": "logged out"}), 200


@bp.post("/logout_all")
@requires_auth
@limiter.limit("10 per minute", key_func=user_or_ip)
def logout_all() -> tuple[object, int]:
    """Revoke all refresh tokens for the authenticated user."""

    try:
        user_id = int(g.current_user_id)
    except (TypeError, ValueError):  # pragma: no cover - guard should ensure int convertible
        return jsonify({"detail": "invalid user"}), 400

    revoke_all_for_user(user_id)
    session.pop("token", None)
    log.info(
        "logout all ok",
        extra={"event": "logout_all_ok", "user_id": user_id, "status": 200},
    )
    return jsonify({"detail": "all sessions revoked"}), 200
