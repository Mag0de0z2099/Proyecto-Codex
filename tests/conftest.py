import os
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def app():
    os.environ.setdefault("FLASK_ENV", "testing")
    # Usa SQLite en memoria si tu app lee DATABASE_URL
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

    try:
        from app import create_app
        flask_app = create_app()
    except Exception:
        from app import app as flask_app
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()
