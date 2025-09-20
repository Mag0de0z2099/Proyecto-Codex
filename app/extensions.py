"""Extensiones compartidas para autenticación."""

from __future__ import annotations

from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect

from .db import db

bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, headers_enabled=True, default_limits=[])


def init_auth_extensions(app):
    """Inicializa las extensiones relacionadas con autenticación."""
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
