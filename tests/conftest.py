import os
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.extensions import limiter
from app.models import User


@pytest.fixture()
def app():
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("APP_ENV", "testing")
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ.setdefault("SECRET_KEY", "test")

    flask_app = create_app()
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with flask_app.app_context():
        db.create_all()
        try:
            yield flask_app
        finally:
            db.session.remove()
            db.drop_all()
            try:
                limiter.reset()
            except Exception:
                pass


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


@pytest.fixture()
def app_ctx(app):
    with app.app_context():
        db.create_all()
        try:
            yield
        finally:
            db.session.remove()
            db.drop_all()
            try:
                limiter.reset()
            except Exception:
                pass


@pytest.fixture()
def make_user(app):
    def _mk(
        email: str = "admin@admin.com",
        username: str = "admin",
        password: str = "admin123",
        role: str = "admin",
        flags: bool = True,
    ) -> User:
        user = User(email=email)
        if hasattr(User, "username"):
            user.username = username
        if hasattr(user, "role"):
            user.role = role
        if hasattr(user, "set_password"):
            user.set_password(password)
        else:
            from werkzeug.security import generate_password_hash

            user.password_hash = generate_password_hash(password)

        flag_values = {
            "is_active": True,
            "active": True,
            "approved": True,
            "is_approved": True,
            "email_verified": True,
            "status": "approved",
        }
        if flags:
            for attr, value in flag_values.items():
                if hasattr(user, attr):
                    setattr(user, attr, value)

        db.session.add(user)
        db.session.commit()
        return user

    return _mk
