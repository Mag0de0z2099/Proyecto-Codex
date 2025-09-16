from app.main import app


def test_home_returns_text():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert "Hola desde Elyra + Render 🚀" in response.get_data(as_text=True)


def test_health_route_returns_ok():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "ok"
