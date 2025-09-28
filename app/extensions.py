"""Extensiones compartidas para autenticación y utilidades globales."""

from __future__ import annotations

import os

from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
csrf = CSRFProtect()

# Base de datos
db = SQLAlchemy()

# Rate limiting (lazy init, se inicializa en create_app)
limiter = Limiter(key_func=get_remote_address, headers_enabled=True, default_limits=[])


def init_auth_extensions(app):
    """Inicializa las extensiones relacionadas con autenticación."""
    bcrypt.init_app(app)
    login_manager.init_app(app)
    if os.getenv("DISABLE_SECURITY") != "1" and app.config.get("WTF_CSRF_ENABLED", True):
        csrf.init_app(app)
