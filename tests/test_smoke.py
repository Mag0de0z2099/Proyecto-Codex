
def test_app_starts(app):
    assert app is not None


def test_root_endpoint(client):
    """No todas las apps exponen '/', por eso aceptamos 200/302/404."""
    res = client.get("/")
    assert res.status_code in (200, 302, 404)
