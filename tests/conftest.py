"""Configuración compartida para las pruebas."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


# Aseguramos que la raíz del proyecto esté en sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def app(monkeypatch, tmp_path):
    """Instancia de la aplicación configurada para pruebas con DB temporal."""

    monkeypatch.setenv("ADMIN_PASSWORD", "pass123")
    monkeypatch.setenv("SECRET_KEY", "tests-secret")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))

    from app import create_app
    from app import db

    application = create_app("test")
    ctx = application.app_context()
    ctx.push()
    db.create_all()

    yield application

    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture
def client(app):
    """Cliente de pruebas basado en la aplicación de testing."""

    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def db_session(app):
    from app import db

    try:
        yield db.session
    finally:
        db.session.rollback()
