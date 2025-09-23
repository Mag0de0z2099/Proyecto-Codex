
def test_app_instance(app):
    """La app debe instanciarse correctamente."""
    assert app is not None


def test_root_endpoint(client):
    """El endpoint raíz debe responder, aunque sea 404 si no está definido."""
    res = client.get("/")
    assert res.status_code in (200, 302, 404)
