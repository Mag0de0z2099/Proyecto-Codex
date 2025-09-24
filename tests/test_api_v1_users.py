import os
import pytest


@pytest.fixture
def app():
    # App fresca por prueba
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    try:
        from app import create_app
        _app = create_app()
    except Exception:
        from app import app as _app  # fallback
    _app.testing = True
    return _app


def test_users_fake_backend_returns_list(client, app, monkeypatch):
    # Fuerza backend 'fake' vía config (no toca DB)
    app.config["FAKE_USERS"] = True
    res = client.get("/api/v1/users")
    assert res.status_code == 200 and res.is_json
    data = res.get_json()
    assert isinstance(data.get("users"), list)
    assert len(data["users"]) >= 2
    assert "email" in data["users"][0]


def test_users_db_path_graceful(client, app, monkeypatch):
    # Asegura que SIN FAKE no explote aunque no haya DB viable
    app.config["FAKE_USERS"] = False
    os.environ.pop("FAKE_USERS", None)
    res = client.get("/api/v1/users")
    assert res.status_code == 200 and res.is_json
    data = res.get_json()
    assert "users" in data
    assert isinstance(data["users"], list)
