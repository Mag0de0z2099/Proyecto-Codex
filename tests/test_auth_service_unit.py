import os
import sys
import types
import pytest

import app.services.auth_service as svc


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


def _inject_fake_modules(monkeypatch, fake_user):
    """
    Inyecta módulos falsos 'app.db' y 'app.models' para que:
      from app.db import db
      from app.models import User
    funcionen dentro de auth_service.verify_credentials.
    """
    class FakeQuery:
        def __init__(self, user):
            self._user = user
        def filter(self, *args, **kwargs):
            return self
        def filter_by(self, **kwargs):
            return self
        def first(self):
            return self._user

    class FakeSession:
        def __init__(self, user):
            self._user = user
        def query(self, _User):
            return FakeQuery(self._user)

    fake_db_module = types.SimpleNamespace(
        db=types.SimpleNamespace(session=FakeSession(fake_user))
    )
    fake_models_module = types.SimpleNamespace(User=object)

    monkeypatch.setitem(sys.modules, "app.db", fake_db_module)
    monkeypatch.setitem(sys.modules, "app.models", fake_models_module)


# ---------- FAKE path ----------
def test_verify_credentials_fake_success(app):
    app.config["FAKE_AUTH"] = True
    user = svc.verify_credentials("admin@admin.com", "admin123", app=app)
    assert user and user["email"] == "admin@admin.com"

def test_verify_credentials_fake_invalid(app):
    app.config["FAKE_AUTH"] = True
    user = svc.verify_credentials("nope@site.com", "bad", app=app)
    assert user is None


# ---------- REAL path (simulado con módulos falsos) ----------
def test_verify_credentials_real_success_check_password(app, monkeypatch):
    app.config["FAKE_AUTH"] = False
    fake_user = types.SimpleNamespace(
        id=10, email="neo@matrix.io", role="user",
        check_password=lambda pw: pw == "good"
    )
    _inject_fake_modules(monkeypatch, fake_user)
    user = svc.verify_credentials("neo@matrix.io", "good", app=app)
    assert user and user["email"] == "neo@matrix.io"

def test_verify_credentials_real_success_plain_password(app, monkeypatch):
    app.config["FAKE_AUTH"] = False
    fake_user = types.SimpleNamespace(
        id=11, email="trinity@matrix.io", role="user", password="love"
    )
    _inject_fake_modules(monkeypatch, fake_user)
    user = svc.verify_credentials("trinity@matrix.io", "love", app=app)
    assert user and user["email"] == "trinity@matrix.io"

def test_verify_credentials_real_user_not_found(app, monkeypatch):
    app.config["FAKE_AUTH"] = False
    _inject_fake_modules(monkeypatch, fake_user=None)
    user = svc.verify_credentials("ghost@matrix.io", "whatever", app=app)
    assert user is None

def test_verify_credentials_real_wrong_password(app, monkeypatch):
    app.config["FAKE_AUTH"] = False
    fake_user = types.SimpleNamespace(
        id=12, email="smith@matrix.io", role="agent",
        check_password=lambda pw: False,  # falla hash
        password=None                      # y tampoco password plano
    )
    _inject_fake_modules(monkeypatch, fake_user)
    user = svc.verify_credentials("smith@matrix.io", "wrong", app=app)
    assert user is None
