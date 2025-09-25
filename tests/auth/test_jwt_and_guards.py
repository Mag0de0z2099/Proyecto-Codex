from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import User


def _user(email, pwd, approved=True, role="user"):
    user = User(
        email=email,
        username=email.split("@", 1)[0],
        password_hash=generate_password_hash(pwd),
        is_active=True,
        is_approved=approved,
    )
    try:
        user.role = role
    except Exception:
        pass
    db.session.add(user)
    db.session.commit()
    return user


def _login(client, email, pwd):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    data = response.get_json() or {}
    return response, data.get("access_token")


def test_me_requires_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_login_returns_jwt_and_me_ok(client, app_ctx):
    _user("adm@a.com", "x", role="admin")
    response, token = _login(client, "adm@a.com", "x")
    assert response.status_code == 200
    assert token

    response_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response_me.status_code == 200
    assert response_me.get_json()["role"] in ("admin", "user")


def test_admin_guard_allows_and_blocks(client, app_ctx):
    _user("admin@a.com", "x", role="admin")
    _, token_admin = _login(client, "admin@a.com", "x")
    allowed = client.get("/api/v1/users?status=pending", headers={"Authorization": f"Bearer {token_admin}"})
    assert allowed.status_code == 200

    _user("user@a.com", "x", role="user")
    _, token_user = _login(client, "user@a.com", "x")
    forbidden = client.get("/api/v1/users?status=pending", headers={"Authorization": f"Bearer {token_user}"})
    assert forbidden.status_code == 403


def test_approve_requires_auth(client, app_ctx):
    response = client.patch("/api/v1/users/999/approve")
    assert response.status_code == 401
