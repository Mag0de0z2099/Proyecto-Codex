from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

from app import create_app
from app.db import db
from app.models import User


def _create_app_with_admin(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    app = create_app("test")
    with app.app_context():
        db.create_all()
        admin = User(
            username="admin",
            email="admin@example.com",
            role="admin",
            is_admin=True,
            status="approved",
            is_active=True,
            approved_at=datetime.now(timezone.utc),
        )
        admin.set_password("pass123")
        db.session.add(admin)
        db.session.commit()
    return app


def test_admin_files_listing(tmp_path, monkeypatch):
    app = _create_app_with_admin(tmp_path, monkeypatch)
    data_dir = Path(app.config["DATA_DIR"])
    reports = data_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    sample = reports / "report.txt"
    sample.write_text("hola")

    client = app.test_client()
    try:
        client.post(
            "/auth/login",
            data={"username": "admin", "password": "pass123"},
            follow_redirects=True,
        )

        response = client.get("/admin/files")
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "reports/report.txt" in body
        assert str(data_dir) in body
    finally:
        client.get("/auth/logout")
        with app.app_context():
            db.drop_all()
            db.session.remove()
