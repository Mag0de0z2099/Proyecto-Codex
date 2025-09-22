from __future__ import annotations

from datetime import datetime, timezone

from app.models import User


def test_register_disabled_redirects(client):
    response = client.get("/auth/register", follow_redirects=False)
    assert response.status_code in (302, 303)
    assert "/auth/login" in response.headers.get("Location", "")


def test_signup_creates_pending_user(client, db_session, app):
    app.config["ALLOW_SELF_SIGNUP"] = True
    response = client.post(
        "/auth/register",
        data={
            "username": "nuevo",
            "password": "secreto123",
            "confirm": "secreto123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    user = db_session.query(User).filter_by(username="nuevo").one()
    assert user.status == "pending"
    assert user.is_active is False
    assert user.approved_at is None

    login_resp = client.post(
        "/auth/login",
        data={"username": "nuevo", "password": "secreto123"},
        follow_redirects=True,
    )
    assert login_resp.status_code == 200
    assert "pendiente de aprobación".encode() in login_resp.data


def test_admin_can_approve_and_assign_role(client, db_session):
    admin = User(
        username="admin",
        email="admin@example.com",
        role="admin",
        is_admin=True,
        is_active=True,
        status="approved",
    )
    admin.set_password("adminpass")
    admin.approved_at = datetime.now(timezone.utc)
    db_session.add(admin)

    user = User(
        username="juan",
        email="juan@example.com",
        role="viewer",
        status="pending",
        is_admin=False,
        is_active=False,
    )
    user.set_password("clave1234")
    db_session.add(user)
    db_session.commit()

    login = client.post(
        "/auth/login",
        data={"username": "admin", "password": "adminpass"},
        follow_redirects=True,
    )
    assert login.status_code == 200

    approve_resp = client.post(
        f"/admin/users/{user.id}/approve",
        data={"role": "supervisor", "category": "seguridad"},
        follow_redirects=True,
    )
    assert approve_resp.status_code == 200

    db_session.refresh(user)
    assert user.status == "approved"
    assert user.is_active is True
    assert user.role == "supervisor"
    assert user.category == "seguridad"
    assert user.approved_at is not None

    client.post("/auth/logout", follow_redirects=True)
    login_user = client.post(
        "/auth/login",
        data={"username": "juan", "password": "clave1234"},
        follow_redirects=True,
    )
    assert login_user.status_code == 200
    assert b"Bienvenido" in login_user.data
