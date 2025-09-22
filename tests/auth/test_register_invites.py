from __future__ import annotations

from app.models import Invite, User
from app.db import db


def test_register_requires_token_in_invite_mode(client, app):
    app.config["SIGNUP_MODE"] = "invite"
    response = client.get("/auth/register")
    assert response.status_code in (302, 303)
    assert "/auth/login" in response.headers.get("Location", "")


def test_register_with_valid_invite_creates_pending_user(client, app):
    app.config["SIGNUP_MODE"] = "invite"
    invite = Invite(token="valid-token", email="test@example.com", max_uses=1)
    db.session.add(invite)
    db.session.commit()

    response = client.post(
        "/auth/register?token=valid-token",
        data={
            "username": "newuser",
            "password": "StrongPass123",
            "confirm": "StrongPass123",
            "email": "test@example.com",
            "token": "valid-token",
        },
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)
    assert "/auth/login" in response.headers.get("Location", "")

    created = User.query.filter_by(username="newuser").first()
    assert created is not None
    assert created.is_active is False
    assert getattr(created, "status", "pending") == "pending"
    db.session.refresh(invite)
    assert invite.used_count == 1


def test_register_open_mode_blocks_non_allowlisted_domain(client, app):
    app.config["SIGNUP_MODE"] = "open"
    app.config["ALLOWLIST_DOMAINS"] = ["empresa.com"]

    response = client.post(
        "/auth/register",
        data={
            "username": "openuser",
            "password": "StrongPass123",
            "confirm": "StrongPass123",
            "email": "otro@otrodominio.com",
        },
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)
    assert "/auth/login" in response.headers.get("Location", "")
    assert User.query.filter_by(username="openuser").first() is None

    # allow valid domain to ensure list works when satisfied
    response_ok = client.post(
        "/auth/register",
        data={
            "username": "openuser",
            "password": "StrongPass123",
            "confirm": "StrongPass123",
            "email": "persona@empresa.com",
        },
        follow_redirects=False,
    )

    assert response_ok.status_code in (302, 303)
    assert "/auth/login" in response_ok.headers.get("Location", "")
    created_open = User.query.filter_by(username="openuser").first()
    assert created_open is not None
    assert getattr(created_open, "status", "pending") == "pending"
    assert created_open.is_active is False
