from app.models import User
from app.blueprints.auth import routes as auth_routes


def test_find_user_by_identifier_email(make_user, app):
    created = make_user(email="user@x.com", username="userx", password="p")
    with app.app_context():
        found = auth_routes.find_user_by_identifier("user@x.com")
        assert found is not None and found.id == created.id
        found_upper = auth_routes.find_user_by_identifier("USER@X.COM")
        assert found_upper is not None and found_upper.id == created.id


def test_find_user_by_identifier_username(make_user, app):
    created = make_user(email="a@a.com", username="adm", password="p")
    with app.app_context():
        if hasattr(User, "username"):
            found = auth_routes.find_user_by_identifier("adm")
            assert found is not None and found.id == created.id


def test_login_flags_bloquean_si_no_aprobado(client, app, make_user):
    app.config["AUTH_SIMPLE"] = False
    make_user(email="p@y.com", username="py", flags=False, password="pass")

    response = client.post(
        "/auth/login",
        data={"username": "py", "password": "pass"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers.get("Location", "").endswith("/auth/login")
    with client.session_transaction() as sess:
        assert "_user_id" not in sess


def test_login_success_email(client, app, make_user):
    app.config["AUTH_SIMPLE"] = False
    make_user(email="admin@admin.com", username="admin", password="admin123")

    response = client.post(
        "/auth/login",
        data={"username": "admin@admin.com", "password": "admin123"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert sess.get("_user_id") is not None
