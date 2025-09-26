def test_health_endpoint_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.is_json
    payload = response.get_json()
    assert payload.get("status") == "ok"
