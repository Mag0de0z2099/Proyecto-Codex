from __future__ import annotations

import pytest

from app import create_app, db


@pytest.fixture()
def dev_client(monkeypatch):
    monkeypatch.setenv("DISABLE_SECURITY", "1")
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with app.app_context():
        db.create_all()

    with app.test_client() as client:
        yield client

    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_dev_mode_allows_internal_routes(dev_client):
    for path in ("/equipos", "/partes", "/checklists", "/operadores"):
        response = dev_client.get(path)
        assert response.status_code not in (401, 403)
