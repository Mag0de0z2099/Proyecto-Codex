from __future__ import annotations

import pytest
from datetime import datetime, timezone

from app import create_app
from app.db import db
from app.models import User


@pytest.fixture()
def app_with_viewer(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    app = create_app("test")
    with app.app_context():
        db.drop_all()
        db.create_all()
        viewer = User(
            username="viewer",
            email="viewer@example.com",
            role="viewer",
            is_admin=False,
            status="approved",
            is_active=True,
            approved_at=datetime.now(timezone.utc),
        )
        viewer.set_password("viewer12345")
        db.session.add(viewer)
        db.session.commit()
    yield app
    with app.app_context():
        db.drop_all()
        db.session.remove()


def test_admin_projects_requires_privileged_role(app_with_viewer):
    client = app_with_viewer.test_client()

    login = client.post(
        "/auth/login",
        data={"username": "viewer", "password": "viewer12345"},
        follow_redirects=False,
    )
    assert login.status_code in (302, 303)

    projects = client.get("/admin/projects")
    assert projects.status_code == 403
