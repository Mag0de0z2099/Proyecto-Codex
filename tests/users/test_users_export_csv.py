from __future__ import annotations

from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import User


def _ensure_admin(email: str = "admin@test.com", password: str = "secret") -> User:
    admin = User.query.filter_by(email=email).one_or_none()
    if admin is None:
        admin = User(
            email=email,
            username="admin",
            password_hash=generate_password_hash(password),
            is_active=True,
            is_approved=True,
        )
        db.session.add(admin)
    else:
        admin.password_hash = generate_password_hash(password)
        admin.is_active = True
        admin.is_approved = True
    try:
        admin.role = "admin"
    except Exception:
        pass
    try:
        admin.status = "approved"
    except Exception:
        pass
    db.session.commit()
    return admin


def _login(client, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return (response.get_json() or {}).get("access_token", "")


def _create_users(count: int = 4) -> None:
    for index in range(count):
        approved = index % 2 == 0
        user = User(
            email=f"user{index}@example.com",
            username=f"user{index}",
            password_hash=generate_password_hash("secret"),
            is_active=True,
            is_approved=approved,
        )
        if approved:
            user.approved_at = datetime.now(timezone.utc)
        try:
            user.role = "user"
        except Exception:
            pass
        try:
            user.status = "approved" if approved else "pending"
        except Exception:
            pass
        db.session.add(user)
    db.session.commit()


def test_api_export_csv(client, app_ctx):
    password = "secret"
    _ensure_admin(password=password)
    _create_users(4)

    token = _login(client, "admin@test.com", password)
    assert token, "login should provide a JWT token"

    response = client.get(
        "/api/v1/users/export.csv?status=approved",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "text/csv" in (response.headers.get("Content-Type") or "")
    payload = response.data.decode()
    assert payload.startswith("id,email,is_approved,approved_at")
    assert "user0@example.com" in payload
    assert "user1@example.com" not in payload


def test_admin_users_csv_requires_login(client, app_ctx):
    response = client.get("/admin/users.csv")
    assert response.status_code in {302, 303}
