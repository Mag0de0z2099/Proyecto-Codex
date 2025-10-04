def test_dev_reset_admin_works_in_dev(app, client, monkeypatch):
    app.config["LOGIN_DISABLED"] = True
    monkeypatch.setenv("DEV_RESET_TOKEN", "tok")
    response = client.get("/auth/dev-reset-admin?token=tok")
    assert response.status_code == 200
    assert "OK: admin reset" in response.data.decode()


def test_dev_reset_admin_hidden_in_prod(app, client, monkeypatch):
    app.config["LOGIN_DISABLED"] = False
    monkeypatch.setenv("DEV_RESET_TOKEN", "tok")
    response = client.get("/auth/dev-reset-admin?token=tok")
    assert response.status_code in (403, 404)


def test_login_after_reset(app, client, monkeypatch):
    app.config["LOGIN_DISABLED"] = True
    monkeypatch.setenv("DEV_RESET_TOKEN", "tok")
    monkeypatch.setenv("DEV_ADMIN_EMAIL", "admin@admin.com")
    monkeypatch.setenv("DEV_ADMIN_PASS", "admin123")
    client.get("/auth/dev-reset-admin?token=tok")
    app.config["LOGIN_DISABLED"] = False

    assert client.get("/auth/login").status_code == 200

    response = client.post(
        "/auth/login",
        data={"email": "admin@admin.com", "password": "admin123"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
