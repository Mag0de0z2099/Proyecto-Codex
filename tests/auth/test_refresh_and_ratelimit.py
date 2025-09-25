from __future__ import annotations

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import User


def _create_user(email: str, password: str, role: str = "admin") -> User:
    user = User(
        email=email,
        username=email.split("@", 1)[0],
        password_hash=generate_password_hash(password),
        is_active=True,
        is_approved=True,
    )
    if hasattr(user, "role"):
        user.role = role
    if hasattr(user, "status"):
        user.status = "approved"
    db.session.add(user)
    db.session.commit()
    return user


def _login(client, email: str, password: str):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    payload = response.get_json() or {}
    return response.status_code, payload.get("access_token"), payload.get("refresh_token")


def test_refresh_flow(client, app_ctx):
    _create_user("refresh@example.com", "secret")
    status, access_token, refresh_token = _login(client, "refresh@example.com", "secret")

    assert status == 200
    assert access_token
    assert refresh_token

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    new_payload = refresh_response.get_json() or {}

    assert refresh_response.status_code == 200
    assert new_payload.get("access_token")
    assert new_payload.get("refresh_token")


def test_rate_limit_login(client, app_ctx):
    _create_user("ratelimit@example.com", "secret")

    for _ in range(5):
        client.post(
            "/api/v1/auth/login",
            json={"email": "ratelimit@example.com", "password": "wrong"},
        )

    sixth_response = client.post(
        "/api/v1/auth/login",
        json={"email": "ratelimit@example.com", "password": "wrong"},
    )

    assert sixth_response.status_code == 429
