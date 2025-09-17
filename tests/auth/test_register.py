from __future__ import annotations

import pytest

from app import create_app
from app.db import db as _db
from app.models.user import User


@pytest.fixture()
def app():
    app = create_app("test")
    with app.app_context():
        _db.drop_all()
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def test_register_success(app, client):
    r = client.post(
        "/auth/register",
        data={
            "email": "nuevo@codex.local",
            "password": "secreto123",
            "confirm": "secreto123",
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"Cuenta creada" in r.data

    # Verificamos en DB
    from app.db import db

    with app.app_context():
        u = db.session.query(User).filter_by(email="nuevo@codex.local").one_or_none()
        assert u is not None
        assert u.check_password("secreto123") is True


def test_register_duplicate_email(app, client):
    from app.db import db

    with app.app_context():
        u = User(email="dup@codex.local", is_admin=False)
        u.set_password("cualquiera123")
        db.session.add(u)
        db.session.commit()

    r = client.post(
        "/auth/register",
        data={
            "email": "dup@codex.local",
            "password": "nuevo12345",
            "confirm": "nuevo12345",
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"ya est\xc3\xa1 registrado" in r.data  # "ya está registrado"


def test_register_password_mismatch(client):
    r = client.post(
        "/auth/register",
        data={
            "email": "mismatch@codex.local",
            "password": "uno12345",
            "confirm": "dos12345",
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"no coinciden" in r.data


def test_register_short_password(client):
    r = client.post(
        "/auth/register",
        data={
            "email": "short@codex.local",
            "password": "123",
            "confirm": "123",
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"al menos 8" in r.data


def test_register_bad_email(client):
    r = client.post(
        "/auth/register",
        data={
            "email": "sin-arroba",
            "password": "secreto123",
            "confirm": "secreto123",
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"Email inv\xc3\xa1lido" in r.data  # "Email inválido"
