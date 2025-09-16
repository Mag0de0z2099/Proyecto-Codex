"""Pruebas para la autenticación del área administrativa."""

from __future__ import annotations

from app import create_app


def test_admin_requires_auth() -> None:
    app = create_app("test")
    client = app.test_client()

    response = client.get("/admin/")

    assert response.status_code == 401
    payload = response.get_json()
    assert payload == {"error": "unauthorized"}


def test_admin_login_ok_and_access() -> None:
    app = create_app("test")
    client = app.test_client()

    response = client.post("/admin/login", json={"password": "admin"})

    assert response.status_code == 200
    assert response.get_json() == {"ok": True}

    response = client.get("/admin/")

    assert response.status_code == 200
    assert response.get_json() == {"area": "admin", "status": "ok"}

    response = client.post("/admin/logout")

    assert response.status_code == 200
    assert response.get_json() == {"ok": True}

    response = client.get("/admin/")

    assert response.status_code == 401
    assert response.get_json() == {"error": "unauthorized"}


def test_admin_login_wrong_password() -> None:
    app = create_app("test")
    client = app.test_client()

    response = client.post("/admin/login", json={"password": "wrong"})

    assert response.status_code == 401
    payload = response.get_json()
    assert payload == {"ok": False, "error": "bad credentials"}
