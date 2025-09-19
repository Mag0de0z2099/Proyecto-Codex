from app import create_app
from app.db import db
from app.models import User


def setup_app():
    app = create_app("test")
    with app.app_context():
        db.drop_all()
        db.create_all()
        u = User(
            username="force",
            email="force@codex.local",
            role="viewer",
            is_admin=False,
            force_change_password=True,
        )
        u.set_password("secreto123")
        db.session.add(u)
        db.session.commit()
    return app


def test_force_change_redirects_to_change_password():
    app = setup_app()
    client = app.test_client()
    response = client.post(
        "/auth/login",
        data={"username": "force", "password": "secreto123"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert "/auth/change-password" in response.headers.get("Location", "")


def test_change_password_clears_flag():
    app = setup_app()
    client = app.test_client()
    client.post(
        "/auth/login",
        data={"username": "force", "password": "secreto123"},
        follow_redirects=True,
    )
    response = client.post(
        "/auth/change-password",
        data={
            "current": "secreto123",
            "new": "nuevo12345",
            "confirm": "nuevo12345",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    client.get("/auth/logout", follow_redirects=True)
    response_login = client.post(
        "/auth/login",
        data={"username": "force", "password": "nuevo12345"},
        follow_redirects=True,
    )
    assert response_login.status_code == 200
