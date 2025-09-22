"""Pruebas para la autenticación del área administrativa con Flask-Login."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from app import create_app
from app.db import db
from app.models import User


@pytest.fixture()
def app_with_admin(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    app = create_app("test")
    with app.app_context():
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
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
    yield app
    with app.app_context():
        db.drop_all()
        db.session.remove()


def test_admin_requires_auth(app_with_admin):
    client = app_with_admin.test_client()

    response = client.get("/admin/")

    assert response.status_code == 302
    assert "/auth/login" in (response.headers.get("Location") or "")


def test_admin_login_ok_and_access(app_with_admin):
    client = app_with_admin.test_client()

    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Dashboard SGC" in response.data

    dashboard = client.get("/admin/")
    assert dashboard.status_code == 200
    assert b"Dashboard SGC" in dashboard.data

    logout = client.get("/auth/logout", follow_redirects=True)
    assert logout.status_code == 200
    assert b"Iniciar sesi" in logout.data

    after_logout = client.get("/admin/")
    assert after_logout.status_code == 302
    assert "/auth/login" in (after_logout.headers.get("Location") or "")


def test_admin_login_wrong_password(app_with_admin):
    client = app_with_admin.test_client()

    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "wrong"},
        follow_redirects=False,
    )

    assert response.status_code == 401
    assert b"Usuario o contrase\xc3\xb1a inv\xc3\xa1lidos" in response.data
