from __future__ import annotations

from flask import request, jsonify
from werkzeug.exceptions import BadRequest, NotFound

from ...db import db
from ...models.user import User
from . import bp


def _validate_email(email: str) -> None:
    if not email or "@" not in email:
        raise BadRequest("email is required and must contain '@'.")


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
    email = (data.get("email") or "").strip()
    _validate_email(email)

    if User.query.filter_by(email=email).first() is not None:
        raise BadRequest("email already exists.")

    u = User(email=email)
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
    email = (data.get("email") or "").strip()
    _validate_email(email)

    if User.query.filter(User.id != user_id, User.email == email).first():
        raise BadRequest("email already exists.")

    u.email = email
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
