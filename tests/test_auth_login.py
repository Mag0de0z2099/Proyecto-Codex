from __future__ import annotations

from app import db
from app.models import User


def _create_user(
    *,
    username: str = "admin",
    email: str = "admin@example.com",
    password: str = "admin123",
    password_hash: str | None = None,
    status: str = "approved",
    is_active: bool = True,
    is_approved: bool = True,
) -> User:
    user = User(
        username=username,
        email=email,
        status=status,
        is_active=is_active,
        is_approved=is_approved,
    )
    if password_hash:
        user.password_hash = password_hash
    else:
        user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def test_login_get_exists(client):
    response = client.get("/auth/login")

    assert response.status_code == 200


def test_seed_admin_and_login_success(app, client):
    app.config.update(LOGIN_DISABLED=False, AUTH_SIMPLE=False)

    result = app.test_cli_runner().invoke(
        args=[
            "users:seed-admin",
            "--email",
            "admin@admin.com",
            "--password",
            "admin123",
        ]
    )
    assert result.exit_code == 0

    login_page = client.get("/auth/login")
    assert login_page.status_code == 200

    response = client.post(
        "/auth/login",
        data={"email": "admin@admin.com", "password": "admin123"},
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)


def test_login_fail_wrong_password(app, client):
    app.config.update(LOGIN_DISABLED=False, AUTH_SIMPLE=False)

    seed = app.test_cli_runner().invoke(
        args=["users:seed-admin", "--email", "admin@admin.com", "--password", "admin123"]
    )
    assert seed.exit_code == 0

    response = client.post(
        "/auth/login",
        data={"email": "admin@admin.com", "password": "wrong"},
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)


def test_login_allows_casefold_email_and_pass_field(app, client):
    app.config.update(LOGIN_DISABLED=False, AUTH_SIMPLE=False)

    with app.app_context():
        _create_user(username="AdminUser", email="admin@example.com", password="secreto")

    response = client.post(
        "/auth/login",
        data={"email": "ADMIN@example.com ", "pass": "secreto"},
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)


def test_login_wrong_password_shows_error(app, client):
    app.config.update(LOGIN_DISABLED=False, AUTH_SIMPLE=False)

    with app.app_context():
        _create_user(username="AdminUser", email="admin@example.com", password="secreto")

    response = client.post(
        "/auth/login",
        data={"username": "AdminUser", "password": "otra"},
        follow_redirects=True,
    )

    assert b"Usuario/contrase\xc3\xb1a incorrectos" in response.data


def test_login_rejected_user_is_blocked(app, client):
    app.config.update(LOGIN_DISABLED=False, AUTH_SIMPLE=False)

    with app.app_context():
        _create_user(
            username="PendingUser",
            email="pending@example.com",
            password="secreto",
            status="rejected",
            is_approved=False,
        )

    response = client.post(
        "/auth/login",
        data={"email": "pending@example.com", "password": "secreto"},
        follow_redirects=True,
    )

    assert b"Tu cuenta est\xc3\xa1 pendiente de aprobaci\xc3\xb3n o inactiva" in response.data
