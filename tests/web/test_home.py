"""Pruebas para las rutas del blueprint web."""

from __future__ import annotations

from app import create_app


def test_home_renders_homepage(client) -> None:
    """La página principal muestra el nuevo branding del SGC."""

    res = client.get("/")

    assert res.status_code == 200

    html = res.get_data(as_text=True)

    assert "Sistema de Gestión de Calidad" in html
    assert "Huasteca Fuel Terminal" in html


def test_health_returns_ok() -> None:
    app = create_app("test")
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.data == b"ok"
