from __future__ import annotations

from app import create_app
from app import db
from app.models import User


def setup_app():
    app = create_app("test")
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app


def test_forgot_generates_link_when_user_exists():
    app = setup_app()
    with app.app_context():
        u = User(
            username="demo",
            email="demo@codex.local",
            role="viewer",
            is_admin=False,
        )
        u.set_password("demo12345")
        db.session.add(u)
        db.session.commit()

    client = app.test_client()
    r = client.post(
        "/auth/forgot-password",
        data={"email": "demo@codex.local"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"/auth/reset-password/" in r.data  # se muestra el link


def test_forgot_neutral_when_user_not_exists():
    app = setup_app()
    client = app.test_client()
    r = client.post(
        "/auth/forgot-password",
        data={"email": "noexiste@codex.local"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    # no debe exponer datos, pero muestra pantalla de enviado
    assert b"Enlace de restablecimiento" in r.data


def test_forgot_password_invalid_email_returns_400_form():
    app = setup_app()
    client = app.test_client()
    r = client.post(
        "/auth/forgot-password",
        data={"email": "invalid"},
        follow_redirects=False,
    )
    assert r.status_code == 400
    assert b"email v\xc3\xa1lido" in r.data


def test_forgot_password_accepts_json_payload():
    app = setup_app()
    with app.app_context():
        u = User(
            username="json-demo",
            email="json@codex.local",
            role="viewer",
            is_admin=False,
        )
        u.set_password("demo12345")
        db.session.add(u)
        db.session.commit()

    client = app.test_client()
    r = client.post(
        "/auth/forgot-password",
        json={"email": "json@codex.local"},
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["ok"] is True
    assert "/auth/reset-password/" in data["reset_url"]


def test_forgot_password_json_invalid_email_returns_400():
    app = setup_app()
    client = app.test_client()
    r = client.post(
        "/auth/forgot-password",
        json={"email": "invalid"},
    )
    assert r.status_code == 400
    data = r.get_json()
    assert data["ok"] is False
    assert "Email" in data["error"]
