import pytest
from flask import Blueprint


def register_test_bp(app):
    from app.authz import requires_role

    if "_test_admin.admin_ping" in app.view_functions:
        return

    bp = Blueprint("_test_admin", __name__)

    @bp.get("/_test/admin/ping")
    @requires_role("admin")
    def admin_ping():
        return "ok", 200

    app.register_blueprint(bp)


def test_requires_role_forbidden_without_role(client, app):
    register_test_bp(app)
    res = client.get("/_test/admin/ping")  # sin header
    assert res.status_code == 403


def test_requires_role_allowed_with_header(client, app):
    register_test_bp(app)
    res = client.get("/_test/admin/ping", headers={"X-Debug-Role": "admin"})
    assert res.status_code == 200
