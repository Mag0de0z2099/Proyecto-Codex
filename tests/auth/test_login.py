from __future__ import annotations

from datetime import datetime, timezone

import pytest
from werkzeug.security import generate_password_hash

from app.db import db
from app.models import User


@pytest.fixture()
def app_ctx(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


def _create_user(email: str, password: str, approved: bool) -> User:
    hashed = generate_password_hash(password)
    user = User(
        username=email.split("@", 1)[0],
        email=email,
        password_hash=hashed,
        is_active=True,
        is_admin=False,
        role="viewer",
        status="approved" if approved else "pending",
        approved_at=datetime.now(timezone.utc) if approved else None,
        is_approved=approved,
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_login_ok_returns_token(client, app_ctx):
    _create_user("a@example.com", "secret", approved=True)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "a@example.com", "password": "secret"},
    )
    payload = response.get_json()
    assert response.status_code == 200
    assert payload == {"token": "dev-token"}


def test_login_not_approved_returns_403(client, app_ctx):
    _create_user("b@example.com", "secret", approved=False)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "b@example.com", "password": "secret"},
    )
    assert response.status_code == 403
    assert response.get_json()["detail"] == "not approved"


def test_login_bad_credentials_returns_401(client, app_ctx):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "secret"},
    )
    assert response.status_code == 401
    assert response.get_json()["detail"] == "invalid credentials"
