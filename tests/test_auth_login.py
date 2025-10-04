from __future__ import annotations


def test_seed_admin_and_login_success(app, client):
    app.config.update(LOGIN_DISABLED=False, AUTH_SIMPLE=False)

    result = app.test_cli_runner().invoke(
        args=[
            "users:seed-admin",
            "--email",
            "admin@admin.com",
            "--password",
            "admin123",
        ]
    )
    assert result.exit_code == 0

    login_page = client.get("/auth/login")
    assert login_page.status_code == 200

    response = client.post(
        "/auth/login",
        data={"email": "admin@admin.com", "password": "admin123"},
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)


def test_login_fail_wrong_password(app, client):
    app.config.update(LOGIN_DISABLED=False, AUTH_SIMPLE=False)

    seed = app.test_cli_runner().invoke(
        args=["users:seed-admin", "--email", "admin@admin.com", "--password", "admin123"]
    )
    assert seed.exit_code == 0

    response = client.post(
        "/auth/login",
        data={"email": "admin@admin.com", "password": "wrong"},
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)
