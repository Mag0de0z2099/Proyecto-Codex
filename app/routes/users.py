import os

from flask import Blueprint, current_app, jsonify, request

from app.security.roles import requires_role
from app.services.user_service import approve_user, list_users

bp = Blueprint("users_v1", __name__, url_prefix="/api/v1")


@bp.get("/users")
def users_list():
    status = request.args.get("status")
    if current_app.config.get("FAKE_USERS") or os.getenv("FAKE_USERS"):
        fake_users = [
            {"id": 1, "email": "alice@example.com", "is_approved": True},
            {"id": 2, "email": "bob@example.com", "is_approved": False},
        ]
        if status == "pending":
            fake_users = [u for u in fake_users if not u["is_approved"]]
        elif status == "approved":
            fake_users = [u for u in fake_users if u["is_approved"]]
        return jsonify({"users": fake_users}), 200

    rows = list_users(status)
    payload = [
        {
            "id": u.id,
            "email": u.email,
            "is_approved": bool(getattr(u, "is_approved", False)),
        }
        for u in rows
    ]
    return jsonify({"users": payload}), 200


@bp.patch("/users/<int:user_id>/approve")
@requires_role("admin")
def users_approve(user_id: int):
    u = approve_user(user_id)
    if not u:
        return jsonify({"detail": "not found"}), 404
    approved_at = None
    if getattr(u, "approved_at", None):
        try:
            approved_at = u.approved_at.isoformat()
            if approved_at.endswith("+00:00"):
                approved_at = approved_at[:-6] + "Z"
        except Exception:
            approved_at = None
    return (
        jsonify(
            {
                "id": u.id,
                "email": u.email,
                "is_approved": bool(getattr(u, "is_approved", False)),
                "approved_at": approved_at,
            }
        ),
        200,
    )
