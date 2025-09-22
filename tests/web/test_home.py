from __future__ import annotations
import pytest

from app import create_app
from app import db


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

    html = rv.get_data(as_text=True)

    # Branding principal
    assert "SGC - Sistema de Gestión de Calidad" in html

    # Contexto del proyecto
    assert "Huasteca Fuel Terminal" in html

    # Botón de "Conoce más acerca de nosotros"
    assert "https://www.dusiglo21.com" in html
    assert "Conoce más acerca de nosotros" in html
