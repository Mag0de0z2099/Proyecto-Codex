from app.main import app


def test_home_returns_text():
    client = app.test_client()
    r = client.get("/")
    assert r.status_code == 200
    assert b"Elyra + Render" in r.data
