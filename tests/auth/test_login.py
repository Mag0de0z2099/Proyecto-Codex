from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from app.db import db
from app.models import User


def _create_user(email: str, password: str, approved: bool) -> User:
    user = User(
        email=email,
        username=email.split("@", 1)[0],
        password_hash=generate_password_hash(password),
        is_active=True,
        is_approved=approved,
        approved_at=(datetime.now(timezone.utc) if approved else None),
    )
    if hasattr(user, "status"):
        user.status = "approved" if approved else "pending"
    db.session.add(user)
    db.session.commit()
    return user


def test_login_ok_returns_token(client, app_ctx):
    _create_user("approved@example.com", "secret", approved=True)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "approved@example.com", "password": "secret"},
    )
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["token"] == "dev-token"


def test_login_not_approved_returns_403(client, app_ctx):
    _create_user("pending@example.com", "secret", approved=False)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "pending@example.com", "password": "secret"},
    )
    assert response.status_code == 403


def test_login_bad_credentials_returns_401(client, app_ctx):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "secret"},
    )
    assert response.status_code == 401
