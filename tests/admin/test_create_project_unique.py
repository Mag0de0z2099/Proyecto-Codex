from __future__ import annotations

import pytest

from app import create_app
from app import db
from app.models import User


@pytest.fixture()
def app_with_admin(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    app = create_app("test")
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(
            username="admin",
            email="admin@example.com",
            role="admin",
            is_admin=True,
        )
        admin.set_password("admin12345")
        db.session.add(admin)
        db.session.commit()
    yield app
    with app.app_context():
        db.drop_all()
        db.session.remove()


@pytest.fixture()
def client(app_with_admin):
    return app_with_admin.test_client()


def login(client):
    return client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin12345"},
        follow_redirects=True,
    )


def test_create_project_duplicate_name_returns_409(client):
    login(client)

    r1 = client.post("/admin/projects", json={"name": "Dragado 2025"})
    assert r1.status_code == 201
    data1 = r1.get_json()
    assert data1["ok"] is True
    assert data1["project"]["name"] == "Dragado 2025"

    r2 = client.post("/admin/projects", json={"name": "Dragado 2025"})
    assert r2.status_code == 409
    data2 = r2.get_json()
    assert data2["ok"] is False
    assert "Ya existe un proyecto" in data2["error"]

    r3 = client.post("/admin/projects", json={"name": ""})
    assert r3.status_code == 400
    data3 = r3.get_json()
    assert data3["ok"] is False
    assert "obligatorio" in data3["error"].lower()
