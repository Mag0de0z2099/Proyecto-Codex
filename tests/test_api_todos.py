"""Basic CRUD coverage tests for the todos API."""

from __future__ import annotations

from app import create_app
from app import db


def test_todos_crud(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    app = create_app("test")
    with app.app_context():
        db.create_all()
    client = app.test_client()
    response = client.get("/api/v1/todos")
    assert response.status_code == 200
    response = client.post("/api/v1/todos", json={"title": "test todo"})
    assert response.status_code in (200, 201)
    todo = response.get_json()
    todo_id = todo.get("id")
    response = client.get("/api/v1/todos")
    assert response.status_code == 200
    assert any(t.get("id") == todo_id for t in response.get_json())
    with app.app_context():
        db.drop_all()
        db.session.remove()
