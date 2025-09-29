def test_operadores_list(client, monkeypatch):
    monkeypatch.setenv("DISABLE_SECURITY", "1")
    response = client.get("/operadores/")
    assert response.status_code in (200, 302)


def test_operadores_create(client, monkeypatch):
    monkeypatch.setenv("DISABLE_SECURITY", "1")
    response = client.post(
        "/operadores/new",
        data={"nombre": "Juan Pérez", "doc_id": "LIC123"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
