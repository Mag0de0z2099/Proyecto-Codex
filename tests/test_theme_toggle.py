def test_theme_toggle_button_on_home(client):
    rv = client.get("/")
    assert rv.status_code == 200
    html = rv.data.decode("utf-8")
    assert 'id="theme-toggle"' in html
    assert 'data-theme' in html


def test_theme_css_has_both_themes(app):
    with app.test_client() as c:
        css = c.get("/static/css/app.css")
    assert css.status_code == 200
    text = css.data.decode("utf-8")
    assert ":root" in text
    assert "[data-theme='light']" in text


def test_theme_toggle_is_not_floating(app):
    with app.test_client() as c:
        css = c.get("/static/css/app.css")
    txt = css.data.decode("utf-8")
    assert "position:fixed" not in txt
