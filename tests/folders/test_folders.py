import os

from datetime import datetime, timezone

from app.models import Folder, Project, User


def _login(client):
    return client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=True,
    )


def test_admin_can_create_folder(app, client, db_session, tmp_path):
    with app.app_context():
        user = User(
            username="admin",
            role="admin",
            is_admin=True,
            is_active=True,
            status="approved",
            approved_at=datetime.now(timezone.utc),
        )
        user.set_password("admin")
        db_session.add(user)

        project = Project(name="Terminal", status="activo")
        db_session.add(project)
        db_session.commit()
        project_id = project.id

    _login(client)

    response = client.get("/admin/folders")
    assert response.status_code == 200
    assert b"Carpetas" in response.data

    fs_dir = tmp_path / "semana_38"
    fs_dir.mkdir()

    create = client.post(
        "/admin/folders",
        data={
            "project_id": project_id,
            "logical_path": "bitacoras/2025/semana_38",
            "fs_path": str(fs_dir),
        },
        follow_redirects=True,
    )
    assert create.status_code == 200
    assert b"Carpeta creada" in create.data

    with app.app_context():
        folder = Folder.query.filter_by(
            project_id=project_id, logical_path="bitacoras/2025/semana_38"
        ).first()
        assert folder is not None
        assert folder.fs_path == os.path.abspath(str(fs_dir))
