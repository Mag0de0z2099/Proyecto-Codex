from app import create_app
from app.db import db
from datetime import datetime, timezone

from app.models import User


def setup_app():
    app = create_app("test")
    with app.app_context():
        db.drop_all()
        db.create_all()
        u = User(
            username="admin",
            email=None,
            role="admin",
            is_admin=True,
            is_active=True,
            status="approved",
            approved_at=datetime.now(timezone.utc),
        )
        u.set_password("admin")
        db.session.add(u)
        db.session.commit()
    return app


def test_login_with_username():
    app = setup_app()
    client = app.test_client()
    r = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)


def test_login_invalid_credentials_returns_401():
    app = setup_app()
    client = app.test_client()
    r = client.post(
        "/auth/login",
        data={"username": "admin", "password": "wrong"},
        follow_redirects=False,
    )
    assert r.status_code == 401
    assert b"Usuario o contrase\xc3\xb1a inv\xc3\xa1lidos" in r.data
