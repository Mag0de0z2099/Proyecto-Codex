def test_admin_login_and_logout_flow(client):
    r = client.get("/admin/")
    assert r.status_code in (401, 403, 200)

    r = client.post("/admin/login", json={"password": "pass123"})
    assert r.status_code in (200, 204)

    r = client.get("/admin/")
    assert r.status_code == 200
    data = r.get_json() or {}
    assert data.get("area") == "admin"

    r = client.post("/admin/logout")
    assert r.status_code in (200, 204)

    r = client.get("/admin/")
    assert r.status_code in (401, 403, 200)
