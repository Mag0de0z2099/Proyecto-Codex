from __future__ import annotations

import os
from pathlib import Path


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT", "dev-salt")
    # Email opcional (si no se configura, se enviará a logs)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587 or 25))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@codex.local")
    # DATA_DIR: si no te dan un disco persistente, usa ./data
    DATA_DIR = Path(os.environ.get("DATA_DIR", Path("data").resolve()))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{DATA_DIR / 'app.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")


class DevConfig(BaseConfig):
    DEBUG = True


class ProdConfig(BaseConfig):
    DEBUG = False


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}


CONFIG_MAP: dict[str, type[BaseConfig]] = {
    "development": DevConfig,
    "production": ProdConfig,
    "testing": TestingConfig,
}

ALIASES = {
    "dev": "development",
    "prod": "production",
    "test": "testing",
}


def get_config(name: str | None) -> type[BaseConfig]:
    env = (
        name
        or os.environ.get("APP_ENV")
        or os.environ.get("FLASK_ENV")
        or os.environ.get("FLASK_CONFIG")
        or "production"
    )
    env = env.lower()
    env = ALIASES.get(env, env)
    return CONFIG_MAP.get(env, CONFIG_MAP["production"])
