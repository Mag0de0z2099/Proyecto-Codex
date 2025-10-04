from __future__ import annotations


def test_dev_mode_flag(app, client):
    app.config["LOGIN_DISABLED"] = True

    response = client.get("/dashboard")

    assert response.status_code == 200
    body = response.data.decode("utf-8")
    assert "Modo DEV" in body
