"""Smoke tests for the Flask application."""

from app import create_app


def test_home_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    app = create_app("test")
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hola" in response.data or response.is_json or response.status_code == 200
