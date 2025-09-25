from __future__ import annotations

import os
from typing import Any

from flask import Blueprint, current_app, jsonify, request

from app.extensions import limiter, user_or_ip
from app.security.guards import requires_auth, requires_role
from app.services.user_service import approve_user as service_approve_user
from app.services.user_service import list_users as service_list_users

bp = Blueprint("users_v1", __name__, url_prefix="/api/v1")


def _parse_positive_int(raw: str | None, default: int, *, upper: int | None = None) -> int:
    try:
        value = int(raw) if raw is not None else default
    except (TypeError, ValueError):
        return default
    if value <= 0:
        value = default
    if upper is not None and value > upper:
        value = upper
    return value


def _serialize_user(user: Any) -> dict[str, Any]:
    return {
        "id": getattr(user, "id", None),
        "email": getattr(user, "email", None),
        "username": getattr(user, "username", None),
        "is_approved": bool(getattr(user, "is_approved", False)),
        "status": getattr(user, "status", None),
    }


@bp.get("/users")
@requires_auth
@requires_role("admin")
@limiter.limit("60 per minute", key_func=user_or_ip)
def list_users():
    """Return users supporting filters, search and pagination."""

    status = request.args.get("status")
    search = request.args.get("q")
    page = _parse_positive_int(request.args.get("page"), 1)
    per_page = _parse_positive_int(request.args.get("per_page"), 10, upper=100)

    if current_app.config.get("FAKE_USERS") or os.getenv("FAKE_USERS"):
        fake_items = [
            {"id": 1, "email": "alice@example.com", "is_approved": True},
            {"id": 2, "email": "bob@example.com", "is_approved": True},
        ]
        meta = {
            "page": page,
            "per_page": per_page,
            "pages": 1,
            "total": len(fake_items),
        }
        return jsonify(items=fake_items, meta=meta, users=fake_items), 200

    try:
        rows, meta = service_list_users(
            status=status,
            search=search,
            page=page,
            per_page=per_page,
        )
    except Exception:
        empty_meta = {"page": page, "per_page": per_page, "pages": 1, "total": 0}
        return jsonify(items=[], meta=empty_meta, users=[]), 200

    data = [_serialize_user(row) for row in rows]
    meta.setdefault("page", page)
    meta.setdefault("per_page", per_page)
    meta.setdefault("pages", 1)
    meta.setdefault("total", len(data))
    return jsonify(items=data, meta=meta, users=data), 200


@bp.patch("/users/<int:user_id>/approve")
@requires_auth
@requires_role("admin")
@limiter.limit("30 per minute", key_func=user_or_ip)
def approve_user(user_id: int):
    try:
        user = service_approve_user(user_id)
    except Exception:
        return jsonify({"detail": "error updating user"}), 500

    if user is None:
        return jsonify({"detail": "not found"}), 404

    if hasattr(user, "to_dict"):
        return jsonify(user=user.to_dict()), 200
    return jsonify({"detail": "approved"}), 200
