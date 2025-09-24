import os
import pytest
from flask import Blueprint


@pytest.fixture
def app():
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    try:
        from app import create_app

        flask_app = create_app()
    except Exception:
        from app import app as flask_app  # type: ignore
    flask_app.testing = True
    return flask_app


def _register_bp(app, required_roles=("admin", "manager")):
    from app.authz import requires_role

    bp = Blueprint("_test_authz", __name__)

    @bp.get("/_test/authz/panel")
    @requires_role(*required_roles)
    def panel():
        return "ok", 200

    app.register_blueprint(bp)


def register_test_bp(app, required_roles=("admin", "manager")):
    _register_bp(app, required_roles=required_roles)


def test_requires_role_forbidden_without_identity(client, app):
    _register_bp(app)
    response = client.get("/_test/authz/panel")
    assert response.status_code == 403


def test_requires_role_allows_debug_header(client, app):
    _register_bp(app)
    response = client.get(
        "/_test/authz/panel",
        headers={"X-Debug-Role": "admin"},
    )
    assert response.status_code == 200


def test_header_is_ignored_when_not_testing(client, app, monkeypatch):
    app.testing = False
    monkeypatch.setenv("FLASK_ENV", "production")

    register_test_bp(app)

    res = client.get(
        "/_test/authz/panel",
        headers={"X-Debug-Role": "admin"},
    )
    assert res.status_code == 403
