from flask import current_app


def test_app_config_loaded(app):
    with app.app_context():
        assert current_app.config.get("SECRET_KEY")
        assert "SQLALCHEMY_DATABASE_URI" in current_app.config
