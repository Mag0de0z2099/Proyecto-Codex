import os
import pytest


@pytest.fixture
def app():
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    try:
        from app import create_app
        _app = create_app()
    except Exception:
        from app import app as _app
    _app.testing = True
    return _app


def test_get_todos_fake_backend(client, app):
    app.config["FAKE_TODOS"] = True
    res = client.get("/api/v1/todos")
    assert res.status_code == 200 and res.is_json
    data = res.get_json()
    assert isinstance(data.get("todos"), list)
    assert len(data["todos"]) >= 2
    assert {"id", "title", "done"} <= set(data["todos"][0].keys())


def test_post_todo_validation_error(client, app):
    app.config["FAKE_TODOS"] = True
    res = client.post("/api/v1/todos", json={})  # faltó title
    assert res.status_code == 400
    assert res.is_json
    data = res.get_json()
    assert data["error"]["code"] == 400


def test_post_todo_created_fake(client, app):
    app.config["FAKE_TODOS"] = True
    res = client.post("/api/v1/todos", json={"title": "Write tests", "done": False})
    assert res.status_code == 201 and res.is_json
    data = res.get_json()
    assert data["todo"]["title"] == "Write tests"
    assert data["todo"]["done"] is False
