"""Endpoints CRUD para el modelo ``Todo``."""

from __future__ import annotations

from flask import jsonify, request

from ....db import db
from ....models import Todo
from . import bp_api_v1


@bp_api_v1.get("/todos")
def list_todos():
    """Listar todas las tareas ordenadas por creación descendente."""

    items = Todo.query.order_by(Todo.id.desc()).all()
    return jsonify([item.to_dict() for item in items])


@bp_api_v1.post("/todos")
def create_todo():
    """Crear una nueva tarea."""

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify(error="title required"), 400
    todo = Todo(title=title, done=bool(data.get("done", False)))
    db.session.add(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 201


@bp_api_v1.get("/todos/<int:todo_id>")
def get_todo(todo_id: int):
    """Obtener el detalle de una tarea."""

    todo = Todo.query.get_or_404(todo_id)
    return jsonify(todo.to_dict())


@bp_api_v1.patch("/todos/<int:todo_id>")
def update_todo(todo_id: int):
    """Actualizar parcialmente una tarea."""

    todo = Todo.query.get_or_404(todo_id)
    data = request.get_json(silent=True) or {}
    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify(error="title required"), 400
        todo.title = title
    if "done" in data:
        todo.done = bool(data.get("done"))
    db.session.commit()
    return jsonify(todo.to_dict())


@bp_api_v1.delete("/todos/<int:todo_id>")
def delete_todo(todo_id: int):
    """Eliminar una tarea."""

    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    return jsonify(ok=True)
