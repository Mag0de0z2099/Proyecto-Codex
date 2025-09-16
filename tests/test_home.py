"""Pruebas para el endpoint principal de la aplicación."""

import importlib


def get_app():
    module = importlib.import_module("app.main")
    return getattr(module, "app")


def test_home_returns_text():
    app = get_app()
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Elyra + Render" in response.data
