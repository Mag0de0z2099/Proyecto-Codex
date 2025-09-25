import os
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import db
from app.extensions import limiter


@pytest.fixture(scope="session")
def app():
    os.environ["FLASK_ENV"] = "testing"
    os.environ["APP_ENV"] = "testing"
    # Usa SQLite en memoria si tu app lee DATABASE_URL
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    try:
        from app import create_app
        flask_app = create_app()
    except Exception:
        from app import app as flask_app
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def app_ctx(app):
    with app.app_context():
        db.create_all()
        try:
            yield
        finally:
            db.session.remove()
            db.drop_all()
            limiter.reset()
