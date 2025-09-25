from __future__ import annotations

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import User


def _mk(count: int = 15, approved: bool = True) -> list[User]:
    rows: list[User] = []
    for i in range(count):
        user = User(
            email=f"user{i}@example.com",
            username=f"user{i}",
            password_hash=generate_password_hash("secret"),
            is_active=True,
            is_approved=approved if i % 2 == 0 else not approved,
        )
        try:
            user.role = "user"
        except Exception:
            pass
        try:
            user.status = "approved" if user.is_approved else "pending"
        except Exception:
            pass
        db.session.add(user)
        rows.append(user)
    db.session.commit()
    return rows


def _login_admin(client) -> str:
    admin = User.query.filter_by(email="admin@test.com").one_or_none()
    if admin is None:
        admin = User(
            email="admin@test.com",
            username="admin",
            password_hash=generate_password_hash("secret"),
            is_active=True,
            is_approved=True,
        )
        db.session.add(admin)
    else:
        admin.password_hash = generate_password_hash("secret")
    try:
        admin.role = "admin"
    except Exception:
        pass
    try:
        admin.status = "approved"
    except Exception:
        pass
    db.session.commit()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "secret"},
    )
    token = (response.get_json() or {}).get("access_token")
    assert token, "login should provide a token"
    return token


def test_users_api_pagination_and_search(client, app_ctx):
    _mk(17)
    token = _login_admin(client)

    response = client.get(
        "/api/v1/users?page=2&per_page=5",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data["items"], list)
    assert len(data["items"]) == 5
    assert data["meta"]["page"] == 2
    assert data["meta"]["per_page"] == 5

    response_search = client.get(
        "/api/v1/users?q=user1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_search.status_code == 200
    data_search = response_search.get_json()
    assert any("user1" in item.get("email", "") for item in data_search["items"])
    assert data_search["meta"]["total"] >= 1
