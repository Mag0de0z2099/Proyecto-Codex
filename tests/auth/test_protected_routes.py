import pytest


@pytest.mark.parametrize("path", ["/equipos", "/partes", "/checklists", "/operadores"])
def test_requires_login(client, path):
    response = client.get(path, follow_redirects=False)
    assert response.status_code in (302, 308, 401)
