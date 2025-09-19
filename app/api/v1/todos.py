from __future__ import annotations

from flask import jsonify, request
from werkzeug.exceptions import BadRequest

from ...db import db
from ...models import Todo
from . import bp


def _parse_payload() -> dict[str, object]:
    payload = request.get_json(silent=True)
    if payload is None:
        raise BadRequest("JSON body required.")
    if not isinstance(payload, dict):
        raise BadRequest("JSON object expected.")
    return payload


@bp.get("/todos")
def list_todos():
    todos = Todo.query.order_by(Todo.id.asc()).all()
    return jsonify([todo.to_dict() for todo in todos])


@bp.post("/todos")
def create_todo():
    payload = _parse_payload()
    title = str(payload.get("title") or "").strip()
    if not title:
        raise BadRequest("title is required")

    todo = Todo(title=title)
    db.session.add(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 201
