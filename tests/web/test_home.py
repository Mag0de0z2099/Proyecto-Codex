"""Pruebas para las rutas del blueprint web."""

from __future__ import annotations

from app import create_app


def test_home_renders_homepage() -> None:
    app = create_app("test")
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert "SGC · Sistema de Gestión de Contratos".encode("utf-8") in response.data


def test_health_returns_ok() -> None:
    app = create_app("test")
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.data == b"ok"
