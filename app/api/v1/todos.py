from flask import Blueprint, jsonify, request, abort, current_app

from app.services.todo_service import list_todos, create_todo

bp = Blueprint("todos_v1", __name__, url_prefix="/api/v1")


@bp.get("/todos")
def get_todos():
    return jsonify(todos=list_todos(current_app)), 200


@bp.post("/todos")
def post_todo():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        abort(400, description="Field 'title' is required and must be a non-empty string.")
    done = bool(data.get("done", False))
    todo = create_todo(title=title, done=done, app=current_app)
    return jsonify(todo=todo), 201
