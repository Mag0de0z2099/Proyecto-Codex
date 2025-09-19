from app import create_app
from app.db import db
from app.models import Folder, Project, User


def setup_app():
    app = create_app("test")
    with app.app_context():
        db.drop_all()
        db.create_all()
        user = User(username="admin", is_admin=True, is_active=True)
        user.set_password("admin")
        db.session.add(user)
        project = Project(name="Terminal", status="activo")
        db.session.add(project)
        db.session.commit()
    return app


def login(client):
    return client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=True,
    )


def test_admin_can_create_folder():
    app = setup_app()
    client = app.test_client()
    login(client)

    response = client.get("/admin/folders")
    assert response.status_code == 200
    assert b"Carpetas" in response.data

    with app.app_context():
        project = Project.query.filter_by(name="Terminal").first()
        assert project is not None

    create = client.post(
        "/admin/folders",
        data={"project_id": project.id, "name": "Planos"},
        follow_redirects=True,
    )
    assert create.status_code == 200
    assert b"Carpeta creada" in create.data

    with app.app_context():
        folder = Folder.query.filter_by(project_id=project.id, name="Planos").first()
        assert folder is not None
