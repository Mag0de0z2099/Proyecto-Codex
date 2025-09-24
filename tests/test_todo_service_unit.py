import pytest

# Importamos el módulo para poder monkeypatchear su estado interno
import app.services.todo_service as svc


@pytest.fixture(autouse=True)
def reset_fake_store(monkeypatch):
    """Aísla el estado del fake store entre tests."""
    monkeypatch.setattr(
        svc,
        "_FAKE_STORE",
        [
            {"id": 1, "title": "Buy milk", "done": False},
            {"id": 2, "title": "Ship feature", "done": True},
        ],
        raising=False,
    )


def test_list_todos_fake_via_config(app):
    app.config["FAKE_TODOS"] = True
    todos = svc.list_todos(app)
    assert isinstance(todos, list)
    assert len(todos) >= 2
    assert {"id", "title", "done"} <= set(todos[0].keys())


def test_list_todos_fake_via_env(monkeypatch):
    # Sin app, activamos por variable de entorno
    monkeypatch.setenv("FAKE_TODOS", "1")
    todos = svc.list_todos(app=None)
    assert len(todos) >= 2


def test_create_todo_fake_increments_id(app):
    app.config["FAKE_TODOS"] = True
    before_max = max(t["id"] for t in svc._FAKE_STORE)
    created = svc.create_todo("Write tests", done=False, app=app)
    assert created["id"] == before_max + 1
    assert any(t["title"] == "Write tests" for t in svc._FAKE_STORE)


def test_list_todos_db_path_graceful_when_no_model(app, monkeypatch):
    """
    Si no existe el modelo/DB usable, list_todos debe devolver [] sin explotar.
    En muchos repos no hay 'Todo' model, lo que fuerza el except.
    """
    app.config["FAKE_TODOS"] = False
    monkeypatch.delenv("FAKE_TODOS", raising=False)
    todos = svc.list_todos(app)
    assert isinstance(todos, list)  # vacío pero válido
    # No aseguramos vacío rígidamente por si sí hay modelo, pero no debe romper.


def test_create_todo_db_path_graceful_when_no_model(app, monkeypatch):
    """
    En el camino 'real' sin modelo/DB, create_todo debe devolver un dict válido
    y no lanzar excepciones (fallback con id None).
    """
    app.config["FAKE_TODOS"] = False
    monkeypatch.delenv("FAKE_TODOS", raising=False)
    todo = svc.create_todo("From DB path", done=True, app=app)
    assert {"id", "title", "done"} <= set(todo.keys())
    # En fallback normalmente id es None; si hay modelo real, será int.
    assert todo["title"] == "From DB path"
