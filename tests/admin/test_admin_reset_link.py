from __future__ import annotations

from app import create_app
from app.db import db
from app.models.user import User


def setup_app():
    app = create_app("test")
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(email="admin@codex.local", is_admin=True)
        admin.set_password("admin12345")
        u = User(email="user@codex.local", is_admin=False)
        u.set_password("user12345")
        db.session.add_all([admin, u])
        db.session.commit()
    return app


def login(client, email, password):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def test_admin_generates_reset_link():
    app = setup_app()
    client = app.test_client()
    login(client, "admin@codex.local", "admin12345")

    r = client.get("/admin/users")
    assert r.status_code == 200
    assert b"user@codex.local" in r.data

    with app.app_context():
        user = db.session.query(User).filter_by(email="user@codex.local").one()
    r2 = client.post(f"/admin/users/{user.id}/reset-link", follow_redirects=True)
    assert r2.status_code == 200
    assert b"/auth/reset-password/" in r2.data
