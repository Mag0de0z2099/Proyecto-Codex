import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def app():
    """
    Devuelve una instancia de Flask para pruebas.
    Intenta importar create_app(); si no existe, busca una variable app.
    Ajusta el import si tu paquete no es 'app'.
    """
    os.environ.setdefault("FLASK_ENV", "testing")

    try:
        # Ruta común: app/__init__.py define create_app()
        from app import create_app

        flask_app = create_app()
    except Exception:
        # Fallback: módulo con variable global 'app' (wsgi.py o similar)
        try:
            from app import app as flask_app  # type: ignore
        except Exception:
            # Si usas wsgi.py como entrada
            from wsgi import app as flask_app  # type: ignore

    flask_app.config.setdefault("TESTING", True)
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app):
    """Provee una sesión de base de datos aislada por prueba."""
    from app.db import db

    with app.app_context():
        db.drop_all()
        db.create_all()
        try:
            yield db.session
            db.session.commit()
        finally:
            db.session.rollback()
            db.drop_all()
            db.session.remove()
