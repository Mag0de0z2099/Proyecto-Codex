from __future__ import annotations

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import User


def _admin(email: str = "adm@a.com", pwd: str = "x") -> User:
    user = User(
        email=email,
        username=email,
        password_hash=generate_password_hash(pwd),
        is_active=True,
        is_approved=True,
    )
    try:
        user.role = "admin"
    except Exception:  # pragma: no cover - defensive
        pass
    db.session.add(user)
    db.session.commit()
    return user


def _login(client, email: str, pwd: str) -> tuple[int, str | None, str | None]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": pwd},
    )
    data = response.get_json() or {}
    return response.status_code, data.get("access_token"), data.get("refresh_token")


def test_refresh_rotation_blocks_reuse(client, app_ctx):
    _admin()
    status, access_token, refresh_token = _login(client, "adm@a.com", "x")
    assert status == 200 and access_token and refresh_token

    first = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    first_payload = first.get_json() or {}
    assert first.status_code == 200 and first_payload.get("refresh_token")

    second = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert second.status_code == 401


def test_logout_and_logout_all(client, app_ctx):
    _admin("adm2@a.com")
    status, access_token, refresh_token = _login(client, "adm2@a.com", "x")
    assert status == 200 and access_token and refresh_token

    logout_resp = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout_resp.status_code == 200

    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse.status_code == 401

    status2, access2, refresh2 = _login(client, "adm2@a.com", "x")
    assert status2 == 200 and access2 and refresh2

    logout_all_resp = client.post(
        "/api/v1/auth/logout_all",
        headers={"Authorization": f"Bearer {access2}"},
    )
    assert logout_all_resp.status_code == 200

    reuse_after_all = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh2})
    assert reuse_after_all.status_code == 401
