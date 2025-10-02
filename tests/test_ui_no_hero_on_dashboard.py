from __future__ import annotations


def test_dashboard_has_no_hero(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    html = response.data.decode()
    assert "hero-img" not in html and "<img" not in html


def test_home_keeps_hero(client):
    response = client.get("/")
    assert response.status_code == 200
    assert 'class="hero-img"' in response.data.decode()
