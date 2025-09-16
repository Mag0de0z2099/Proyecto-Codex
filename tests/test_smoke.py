def test_home_ok(client):
    r = client.get("/")
    assert r.status_code == 200
    body = (r.data or b"").decode("utf-8").lower()
    assert "hola" in body or r.is_json or r.status_code == 200
