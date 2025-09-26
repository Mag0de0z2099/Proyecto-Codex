def test_health_endpoint_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.is_json
    assert r.get_json().get("status") == "ok"
