from __future__ import annotations

from datetime import datetime, timezone

from app import create_app
from app.db import db
from app.models import User


def setup_app():
    app = create_app("test")
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(
            username="admin",
            email="admin@codex.local",
            role="admin",
            is_admin=True,
            status="approved",
            is_active=True,
            approved_at=datetime.now(timezone.utc),
        )
        admin.set_password("admin12345")
        u = User(
            username="user",
            email="user@codex.local",
            role="viewer",
            is_admin=False,
            status="approved",
            is_active=True,
            approved_at=datetime.now(timezone.utc),
        )
        u.set_password("user12345")
        db.session.add_all([admin, u])
        db.session.commit()
    return app


def login(client, username, password):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def test_admin_generates_reset_link():
    app = setup_app()
    client = app.test_client()
    login(client, "admin", "admin12345")

    r = client.get("/admin/users")
    assert r.status_code == 200
    assert b"user@codex.local" in r.data

    with app.app_context():
        user = db.session.query(User).filter_by(email="user@codex.local").one()
    r2 = client.post(f"/admin/users/{user.id}/reset-link", follow_redirects=True)
    assert r2.status_code == 200
    assert b"/auth/reset-password/" in r2.data
