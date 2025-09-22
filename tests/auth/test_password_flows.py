import pytest
from datetime import datetime, timezone

from app import create_app
from app.db import db
from app.models import User
from app.security import generate_reset_token


@pytest.fixture()
def app():
    app = create_app("test")
    with app.app_context():
        db.drop_all()
        db.create_all()
        # admin + normal
        admin = User(
            username="admin",
            email="admin@codex.local",
            role="admin",
            is_admin=True,
            status="approved",
            is_active=True,
            approved_at=datetime.now(timezone.utc),
        )
        admin.set_password("admin1234")
        user = User(
            username="user",
            email="user@codex.local",
            role="viewer",
            is_admin=False,
            status="approved",
            is_active=True,
            approved_at=datetime.now(timezone.utc),
        )
        user.set_password("user12345")
        db.session.add_all([admin, user])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, username, password):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def test_change_password_ok(client):
    login(client, "user", "user12345")
    r = client.post(
        "/auth/change-password",
        data={"current": "user12345", "new": "nuevo12345", "confirm": "nuevo12345"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    # re-login con nueva
    client.post("/auth/logout", follow_redirects=True)
    r2 = login(client, "user", "nuevo12345")
    assert r2.status_code == 200


def test_reset_password_ok(client, app):
    # generamos token
    with app.app_context():
        token = generate_reset_token("user@codex.local")
    r = client.post(
        f"/auth/reset-password/{token}",
        data={"new": "rest12345", "confirm": "rest12345"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    # login con nueva
    r2 = login(client, "user", "rest12345")
    assert r2.status_code == 200
