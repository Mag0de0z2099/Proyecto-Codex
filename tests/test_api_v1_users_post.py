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


def test_create_user_missing_email(client, app):
    app.config["FAKE_USERS"] = True
    res = client.post("/api/v1/users", json={"password": "secret123"})
    assert res.status_code == 400 and res.is_json
    assert "email" in (res.get_json()["error"]["message"].lower())


def test_create_user_bad_email(client, app):
    app.config["FAKE_USERS"] = True
    res = client.post("/api/v1/users", json={"email": "not-an-email", "password": "secret123"})
    assert res.status_code == 400


def test_create_user_short_password(client, app):
    app.config["FAKE_USERS"] = True
    res = client.post("/api/v1/users", json={"email": "neo@matrix.io", "password": "123"})
    assert res.status_code == 400


def test_create_user_duplicate_409(client, app):
    app.config["FAKE_USERS"] = True
    # primer alta
    r1 = client.post("/api/v1/users", json={"email": "dupe@site.com", "password": "secret123"})
    assert r1.status_code == 201
    # mismo email con distinto case → debe chocar
    r2 = client.post("/api/v1/users", json={"email": "DUPE@site.com", "password": "secret123"})
    assert r2.status_code == 409


def test_create_user_success_201(client, app):
    app.config["FAKE_USERS"] = True
    res = client.post(
        "/api/v1/users",
        json={"email": "new@site.com", "password": "secret123", "role": "manager"},
    )
    assert res.status_code == 201 and res.is_json
    data = res.get_json()
    assert "user" in data and "email" in data["user"]
    assert data["user"]["email"] == "new@site.com"
    assert "password" not in data["user"]  # sanitizado
