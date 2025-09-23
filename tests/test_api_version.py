
def test_api_version_ok(client, app, monkeypatch):
    monkeypatch.setenv("APP_VERSION", "1.2.3")
    monkeypatch.setenv("GIT_SHA", "abc1234")
    res = client.get("/api/version")
    assert res.status_code == 200 and res.is_json
    data = res.get_json()
    assert data["version"] == "1.2.3"
    assert data["commit"] == "abc1234"
    assert "env" in data
