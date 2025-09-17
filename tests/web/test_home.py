from __future__ import annotations
import re

import pytest

from app import create_app
from app.db import db


@pytest.fixture()
def app():
    app = create_app("test")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_homepage_renders(app):
    client = app.test_client()
    rv = client.get("/")
    assert rv.status_code == 200

    html = rv.data.decode("utf-8")

    # Título/branding
    assert "SGC - Sistema de Gestión de Calidad" in html

    # Proyecto/Descripción
    assert "Gas Natural" in html and "Huasteca Fuel Terminal" in html
    assert "control de carpetas" in html or "bitácoras" in html or "reportes" in html

    # Botón/Login visible
    assert re.search(r'>\s*Login\s*<', html, re.IGNORECASE)
