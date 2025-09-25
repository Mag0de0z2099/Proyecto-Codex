"""Tests básicos de configuración CORS para la API."""

from __future__ import annotations


def test_cors_simple_get(client):
    response = client.get("/healthz", headers={"Origin": "http://localhost:3000"})
    # /healthz no está bajo /api, por lo que no debe exponer cabeceras CORS.
    assert "Access-Control-Allow-Origin" not in response.headers


def test_cors_api_preflight(client):
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )

    assert response.status_code in (200, 204)
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
    allow_methods = response.headers.get("Access-Control-Allow-Methods", "")
    assert "POST" in allow_methods
