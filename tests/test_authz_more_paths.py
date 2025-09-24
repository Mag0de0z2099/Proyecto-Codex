import os
import sys
import types
import pytest
from flask import Blueprint, g


@pytest.fixture
def app():
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    try:
        from app import create_app

        _app = create_app()
    except Exception:
        from app import app as _app  # type: ignore
    _app.testing = True
    return _app


def _register_bp(app, inject_user=None, required_roles=("admin", "manager")):
    from app.authz import requires_role

    bp = Blueprint("_test_authz_more", __name__)

    if inject_user is not None:
        @bp.before_app_request
        def _inject():
            g.user = inject_user

    @bp.get("/_test/authz/panel")
    @requires_role(*required_roles)
    def panel():
        return "ok", 200

    app.register_blueprint(bp)


def test_roles_from_g_user_list_allows(client, app):
    class U:
        ...

    u = U()
    u.roles = ["manager", "viewer"]
    _register_bp(app, inject_user=u)
    res = client.get("/_test/authz/panel")
    assert res.status_code == 200


def test_role_from_g_user_forbidden(client, app):
    class U:
        ...

    u = U()
    u.role = "user"
    _register_bp(app, inject_user=u)
    res = client.get("/_test/authz/panel")
    assert res.status_code == 403


def test_role_from_flask_login_current_user(client, app, monkeypatch):
    fake_module = types.SimpleNamespace(
        current_user=types.SimpleNamespace(is_authenticated=True, role="admin")
    )
    monkeypatch.setitem(sys.modules, "flask_login", fake_module)
    _register_bp(app)
    res = client.get("/_test/authz/panel")
    assert res.status_code == 200
