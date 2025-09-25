import os
from datetime import datetime, timezone

import pytest
from werkzeug.security import generate_password_hash

from app.models import User
from app.extensions import db


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


def _admin_headers(client):
    user = User.query.filter_by(email="admin@example.com").one_or_none()
    if user is None:
        user = User(
            email="admin@example.com",
            username="admin",
            password_hash=generate_password_hash("secret"),
            is_active=True,
            is_approved=True,
            approved_at=datetime.now(timezone.utc),
        )
    else:
        user.password_hash = generate_password_hash("secret")
        user.is_approved = True
    if hasattr(user, "role"):
        user.role = "admin"
    if hasattr(user, "status"):
        user.status = "approved"
    db.session.add(user)
    db.session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "secret"},
    )
    token = (response.get_json() or {}).get("access_token")
    assert token, "login should return an access token"
    return {"Authorization": f"Bearer {token}"}


def test_users_fake_backend_returns_list(client, app, monkeypatch, app_ctx):
    # Fuerza backend 'fake' vía config (no toca DB)
    app.config["FAKE_USERS"] = True
    headers = _admin_headers(client)
    res = client.get("/api/v1/users", headers=headers)
    assert res.status_code == 200 and res.is_json
    data = res.get_json()
    assert isinstance(data.get("items"), list)
    assert len(data["items"]) >= 2
    assert "email" in data["items"][0]
    assert "meta" in data
    assert data["meta"]["total"] >= 2


def test_users_db_path_graceful(client, app, monkeypatch, app_ctx):
    # Asegura que SIN FAKE no explote aunque no haya DB viable
    app.config["FAKE_USERS"] = False
    os.environ.pop("FAKE_USERS", None)
    headers = _admin_headers(client)
    res = client.get("/api/v1/users", headers=headers)
    assert res.status_code == 200 and res.is_json
    data = res.get_json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert "meta" in data
