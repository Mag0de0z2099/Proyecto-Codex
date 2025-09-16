from __future__ import annotations
import json
import pytest

from app import create_app
from app.db import db as _db


@pytest.fixture()
def app():
    app = create_app("dev")  # usa DevConfig
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite://",  # en memoria
    )
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def test_create_and_get_user(client):
    # create
    rv = client.post(
        "/api/v1/users",
        data=json.dumps({"email": "alice@example.com"}),
        content_type="application/json",
    )
    assert rv.status_code == 201
    data = rv.get_json()
    assert data["email"] == "alice@example.com"
    user_id = data["id"]

    # get
    rv = client.get(f"/api/v1/users/{user_id}")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["id"] == user_id


def test_list_users(client):
    # seed
    for e in ["a@a.com", "b@b.com", "c@c.com"]:
        client.post("/api/v1/users", json={"email": e})

    rv = client.get("/api/v1/users?page=1&per_page=2")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert data["total"] == 3
    assert len(data["items"]) == 2


def test_update_user(client):
    rv = client.post("/api/v1/users", json={"email": "x@x.com"})
    user_id = rv.get_json()["id"]

    rv = client.put(f"/api/v1/users/{user_id}", json={"email": "y@y.com"})
    assert rv.status_code == 200
    assert rv.get_json()["email"] == "y@y.com"


def test_delete_user(client):
    rv = client.post("/api/v1/users", json={"email": "z@z.com"})
    user_id = rv.get_json()["id"]

    rv = client.delete(f"/api/v1/users/{user_id}")
    assert rv.status_code == 204

    rv = client.get(f"/api/v1/users/{user_id}")
    assert rv.status_code == 404


def test_validation(client):
    rv = client.post("/api/v1/users", json={"email": "invalid"})
    assert rv.status_code == 400
