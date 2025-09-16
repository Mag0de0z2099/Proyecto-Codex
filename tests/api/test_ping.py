"""Pruebas para la API versión 1."""

from __future__ import annotations

from app import create_app


def test_api_ping_returns_ok() -> None:
    app = create_app("test")
    client = app.test_client()

    response = client.get("/api/v1/ping")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {"ok": True, "version": "v1"}
