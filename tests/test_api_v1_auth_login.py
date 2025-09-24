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


def test_login_missing_email(client, app):
    res = client.post("/api/v1/auth/login", json={"password": "secret123"})
    assert res.status_code == 400 and res.is_json
    assert "email" in res.get_json()["error"]["message"].lower()


def test_login_bad_email_format(client, app):
    res = client.post("/api/v1/auth/login", json={"email": "nope", "password": "secret123"})
    assert res.status_code == 400


def test_login_short_password(client, app):
    res = client.post("/api/v1/auth/login", json={"email": "neo@matrix.io", "password": "123"})
    assert res.status_code == 400


def test_login_invalid_credentials_401(client, app, monkeypatch):
    # monkeypatch del servicio para retornar None (credenciales inválidas)
    import app.services.auth_service as svc

    monkeypatch.setattr(svc, "verify_credentials", lambda email, password, app=None: None)
    res = client.post("/api/v1/auth/login", json={"email": "neo@matrix.io", "password": "secret123"})
    assert res.status_code == 401 and res.is_json


def test_login_success_200(client, app, monkeypatch):
    import app.services.auth_service as svc

    fake_user = {"id": 42, "email": "neo@matrix.io", "role": "chosen-one"}
    monkeypatch.setattr(svc, "verify_credentials", lambda email, password, app=None: fake_user)
    os.environ["FAKE_JWT"] = "test-jwt"
    res = client.post("/api/v1/auth/login", json={"email": "neo@matrix.io", "password": "secret123"})
    assert res.status_code == 200 and res.is_json
    data = res.get_json()
    assert data["ok"] is True
    assert data["user"]["email"] == "neo@matrix.io"
    assert data["token"] == "test-jwt"
