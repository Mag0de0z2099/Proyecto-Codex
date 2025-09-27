from __future__ import annotations

from app import db
from app.models import User


def _create_admin(email: str = "admin@admin.com", password: str = "admin123") -> User:
    user = User(
        username="admin",
        email=email,
        is_admin=True,
        is_active=True,
        status="approved",
        is_approved=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def test_login_admin(client):
    client.application.config["AUTH_SIMPLE"] = False

    _create_admin()

    response = client.post(
        "/auth/login",
        data={"email": "admin@admin.com", "password": "admin123"},
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)
