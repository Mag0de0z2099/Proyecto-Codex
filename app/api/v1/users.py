from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from flask import jsonify, request

from werkzeug.exceptions import BadRequest, NotFound

from ...db import db
from ...models import User
from ...auth.roles import ROLES
from . import bp


def _normalize_email(value: Any) -> str | None:
    if value is None:
        return None
    email = str(value).strip()
    if not email:
        return None
    if "@" not in email:
        raise BadRequest("email must contain '@'.")
    if len(email) > 254:
        raise BadRequest("email must be at most 254 characters.")
    return email


def _require_username(value: Any) -> str:
    username = str(value or "").strip()
    if not username:
        raise BadRequest("username is required.")
    if len(username) > 64:
        raise BadRequest("username must be at most 64 characters.")
    return username


def _parse_pagination() -> tuple[int, int]:
    try:
        page = int(request.args.get("page", 1))
        per_page = min(100, int(request.args.get("per_page", 20)))
    except ValueError:
        raise BadRequest("page and per_page must be integers.")
    if page < 1 or per_page < 1:
        raise BadRequest("page and per_page must be positive.")
    return page, per_page


@bp.get("/users")
def list_users():
    page, per_page = _parse_pagination()
    q = User.query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "items": [u.to_dict() for u in q.items],
            "page": q.page,
            "per_page": q.per_page,
            "total": q.total,
        }
    )


@bp.post("/users")
def create_user():
    data = request.get_json(silent=True) or {}
    username = _require_username(data.get("username"))
    email = _normalize_email(data.get("email"))
    password = data.get("password")
    role_raw = str(data.get("role") or "viewer").strip().lower()
    if role_raw not in ROLES:
        raise BadRequest("invalid role.")
    title = data.get("title")
    title_value = None
    if title is not None:
        title_value = str(title).strip()
        if not title_value:
            title_value = None

    if User.query.filter_by(username=username).first() is not None:
        raise BadRequest("username already exists.")

    if email and User.query.filter_by(email=email).first() is not None:
        raise BadRequest("email already exists.")

    category = data.get("category")
    category_value = None
    if category is not None:
        category_value = str(category).strip() or None

    status_raw = str(data.get("status") or "approved").strip().lower()
    if status_raw not in {"pending", "approved", "rejected"}:
        raise BadRequest("invalid status.")

    u = User(
        username=username,
        email=email,
        role=role_raw,
        title=title_value,
        category=category_value,
        status=status_raw,
    )
    if role_raw == "admin":
        u.is_admin = True
    if status_raw == "approved":
        u.is_active = True
        u.approved_at = datetime.now(timezone.utc)
    else:
        u.is_active = False
        u.approved_at = None
    if not password:
        password = secrets.token_urlsafe(12)
    u.set_password(password)

    db.session.add(u)
    db.session.commit()
    return jsonify(u.to_dict()), 201


@bp.get("/users/<int:user_id>")
def get_user(user_id: int):
    u = User.query.get(user_id)
    if not u:
        raise NotFound("user not found")
    return jsonify(u.to_dict())


@bp.put("/users/<int:user_id>")
def update_user(user_id: int):
    u = User.query.get(user_id)
    if not u:
        raise NotFound("user not found")

    data = request.get_json(silent=True) or {}
    password = data.get("password")

    if "username" in data:
        username = _require_username(data.get("username"))
        if User.query.filter(User.id != user_id, User.username == username).first():
            raise BadRequest("username already exists.")
        u.username = username

    if "email" in data:
        email = _normalize_email(data.get("email"))
        if email and User.query.filter(User.id != user_id, User.email == email).first():
            raise BadRequest("email already exists.")
        u.email = email

    if "role" in data:
        role_raw = str(data.get("role") or "").strip().lower()
        if role_raw not in ROLES:
            raise BadRequest("invalid role.")
        u.role = role_raw
        u.is_admin = role_raw == "admin"

    if "title" in data:
        title = data.get("title")
        if title is None:
            u.title = None
        else:
            title_str = str(title).strip()
            u.title = title_str or None

    if "category" in data:
        category = data.get("category")
        if category is None:
            u.category = None
        else:
            u.category = str(category).strip() or None

    if "status" in data:
        status_raw = str(data.get("status") or "").strip().lower()
        if status_raw not in {"pending", "approved", "rejected"}:
            raise BadRequest("invalid status.")
        u.status = status_raw
        if status_raw == "approved":
            u.is_active = True
            if not u.approved_at:
                u.approved_at = datetime.now(timezone.utc)
        else:
            u.is_active = False
            u.approved_at = None

    if password:
        u.set_password(password)

    db.session.commit()
    return jsonify(u.to_dict())


@bp.delete("/users/<int:user_id>")
def delete_user(user_id: int):
    u = User.query.get(user_id)
    if not u:
        raise NotFound("user not found")

    db.session.delete(u)
    db.session.commit()
    return "", 204
