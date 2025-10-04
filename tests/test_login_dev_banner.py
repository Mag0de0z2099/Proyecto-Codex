def test_login_shows_dev_banner_when_login_disabled(app, client):
    app.config["LOGIN_DISABLED"] = True
    response = client.get("/auth/login")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Modo DEV" in html
    assert 'href="/dashboard' in html


def test_login_hides_dev_banner_when_enabled(app, client):
    app.config["LOGIN_DISABLED"] = False
    response = client.get("/auth/login")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Modo DEV" not in html
