def test_dashboard_renders(client):
    """El dashboard responde con el mensaje de bypass seguro."""
    client.application.config["LOGIN_DISABLED"] = True
    rv = client.get("/dashboard/?days=14")
    assert rv.status_code == 200
    html = rv.data.decode("utf-8")
    assert "DASHBOARD OK" in html
    assert "Modo DEV" in html


def test_home_hero_image_has_limit(client):
    """La portada usa la clase que limita el alto de la imagen (siglo21)."""
    rv = client.get("/")
    assert rv.status_code == 200
    html = rv.data.decode("utf-8")
    assert 'class="hero-img"' in html or "hero-img" in html


def test_app_css_has_hero_rule(app):
    """Verifica que en app.css exista la regla de altura máxima para .hero-img."""
    # Asumimos ruta estándar de static
    with app.test_client() as c:
        css = c.get("/static/css/app.css")
    assert css.status_code == 200
    text = css.data.decode("utf-8")
    assert ".hero-img" in text and ("max-height:" in text or "max-height" in text)
