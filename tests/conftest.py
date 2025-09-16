"""Configuración compartida para las pruebas."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest


# Aseguramos que la raíz del proyecto esté en sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def client(monkeypatch):
    """Crear un cliente de pruebas con configuración mínima."""

    monkeypatch.setenv("ADMIN_PASSWORD", "pass123")
    monkeypatch.setenv("SECRET_KEY", "tests-secret")

    module_name = "app.main"
    if module_name in sys.modules:
        module = importlib.reload(sys.modules[module_name])
    else:
        module = importlib.import_module(module_name)
    # Garantizar que la app se refresque tras modificar entornos.
    module = importlib.reload(module)

    app = getattr(module, "app")
    app.config.update(
        TESTING=True,
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", "admin"),
        SECRET_KEY=os.environ.get("SECRET_KEY", app.config.get("SECRET_KEY")),
    )

    with app.test_client() as test_client:
        yield test_client
