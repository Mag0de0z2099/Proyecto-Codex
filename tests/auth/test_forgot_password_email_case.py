from __future__ import annotations

from sqlalchemy import text

from app import create_app
from app.db import db
from app.models import User


def setup_app():
    app = create_app("test")
    with app.app_context():
        db.drop_all()
        db.create_all()
        user = User(
            username="demo",
            email="user@example.com",
            role="viewer",
            is_admin=False,
        )
        user.set_password("demo12345")
        db.session.add(user)
        db.session.commit()
        # Fuerza un email en mayúsculas como pudo haber quedado en producción
        db.session.execute(
            text("UPDATE users SET email = 'USER@EXAMPLE.COM' WHERE id = :id"),
            {"id": user.id},
        )
        db.session.commit()
    return app


def test_forgot_password_normalizes_email_case_insensitive():
    app = setup_app()
    client = app.test_client()

    response = client.post(
        "/auth/forgot-password",
        data={"email": "user@example.com"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"/auth/reset-password/" in response.data

