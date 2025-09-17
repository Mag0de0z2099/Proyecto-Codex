from app import create_app
from app.db import db
from app.models.folder import Folder
from app.models.user import User


def setup_app():
    app = create_app("test")
    with app.app_context():
        db.drop_all()
        db.create_all()
        user = User(username="admin", is_admin=True, is_active=True)
        user.set_password("admin")
        db.session.add(user)
        db.session.commit()
    return app


def login(client):
    return client.post(
        "/auth/login", data={"username": "admin", "password": "admin"}, follow_redirects=True
    )


def test_create_folder_happy_path():
    app = setup_app()
    client = app.test_client()
    login(client)
    client.get("/folders/")
    with app.app_context():
        root = Folder.query.filter_by(is_root=True).first()
        assert root is not None
        response = client.post(
            "/folders/create",
            data={"parent_id": root.id, "name": "Calidad"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        folder = Folder.query.filter_by(parent_id=root.id, slug="calidad").one_or_none()
        assert folder is not None
