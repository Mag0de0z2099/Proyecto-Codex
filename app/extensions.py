"""Extensiones compartidas para autenticación."""

from __future__ import annotations

from flask_bcrypt import Bcrypt
from flask_login import LoginManager

bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def init_auth_extensions(app):
    """Inicializa las extensiones relacionadas con autenticación."""
    bcrypt.init_app(app)
    login_manager.init_app(app)
