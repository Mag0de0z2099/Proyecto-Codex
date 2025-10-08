import os

import pyotp
import pytest


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() not in {"0", "false", "no", "off"}


@pytest.mark.skipif(not _is_truthy(os.getenv("ENABLE_2FA")), reason="2FA disabled")
def test_login_redirects_to_dashboard(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "dummy-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("AUTH_DISABLED", "false")
    monkeypatch.setenv("AUTH_SIMPLE", "false")

    from app import create_app, db
    from app.models.user import User

    app = create_app()
    app.config.update(
        TESTING=True,
        LOGIN_DISABLED=False,
        AUTH_SIMPLE=False,
        WTF_CSRF_ENABLED=False,
    )

    with app.app_context():
        db.create_all()
        user = User(email="admin@admin.com", role="admin", is_active=True)
        if hasattr(user, "username"):
            user.username = "admin"
        if hasattr(user, "status"):
            user.status = "approved"
        if hasattr(user, "is_approved"):
            user.is_approved = True
        user.set_password("admin123")
        db.session.add(user)
        db.session.commit()

        client = app.test_client()

        response_get = client.get("/auth/login")
        assert response_get.status_code == 200

        response_post = client.post(
            "/auth/login",
            data={"email": "admin@admin.com", "password": "admin123"},
            follow_redirects=False,
        )
        assert response_post.status_code in (302, 303)
        location = response_post.headers.get("Location", "")
        assert location.endswith("/auth/totp/setup"), f"Location={location}"

        response_setup = client.get(location)
        assert response_setup.status_code == 200

        response_setup_post = client.post(location, follow_redirects=False)
        assert response_setup_post.status_code in (302, 303)
        verify_location = response_setup_post.headers.get("Location", "")
        assert verify_location.endswith("/auth/totp/verify"), f"Location={verify_location}"

        refreshed_user = User.query.filter_by(email="admin@admin.com").first()
        assert refreshed_user and refreshed_user.totp_secret
        totp = pyotp.TOTP(refreshed_user.totp_secret)
        code = totp.now()

        response_verify = client.post(
            verify_location,
            data={"code": code},
            follow_redirects=False,
        )
        assert response_verify.status_code in (302, 303)
        final_location = response_verify.headers.get("Location", "")
        assert "/dashboard" in final_location, f"Location={final_location}"

        response_dashboard = client.get(final_location, follow_redirects=True)
        assert response_dashboard.status_code == 200, response_dashboard.data.decode()[:300]
