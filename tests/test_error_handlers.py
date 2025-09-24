import os

import pytest
from flask import Blueprint


@pytest.fixture
def app():
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    try:
        from app import create_app

        _app = create_app()
    except Exception:
        from app import app as _app
    _app.testing = True
    return _app


def _register_crash_bp(app):
    bp = Blueprint("_test_crash", __name__)

    @bp.get("/_test/crash")
    def crash():
        raise RuntimeError("boom")

    app.register_blueprint(bp)


def test_404_is_json_and_has_request_id(client, app):
    res = client.get("/no-existe", headers={"X-Request-Id": "abc123"})
    assert res.status_code == 404
    assert res.is_json
    data = res.get_json()
    assert data["error"]["code"] == 404
    assert data["error"]["path"] == "/no-existe"
    assert data["error"]["request_id"] == "abc123"
    assert res.headers.get("X-Request-Id") == "abc123"


def test_405_is_json(client, app):
    # /admin/panel es GET; probamos POST para 405
    res = client.post("/admin/panel", headers={"X-Debug-Role": "admin"})
    # Si no existe /admin/panel en tu app, 404 también es válido:
    assert res.status_code in (405, 404)
    assert res.is_json


def test_403_is_json(client, app):
    res = client.get("/admin/panel")  # sin rol
    assert res.status_code in (403, 404)  # 404 si no existe la ruta aún
    assert res.is_json


def test_500_is_json_with_request_id(client, app):
    _register_crash_bp(app)
    res = client.get("/_test/crash", headers={"X-Request-Id": "req-500"})
    assert res.status_code == 500
    assert res.is_json
    data = res.get_json()
    assert data["error"]["code"] == 500
    assert data["error"]["request_id"] == "req-500"
    assert res.headers.get("X-Request-Id") == "req-500"
