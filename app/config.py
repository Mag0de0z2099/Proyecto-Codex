from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
INSTANCE_DIR = PROJECT_ROOT / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE = INSTANCE_DIR / "sgc.db"
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_SQLITE}"
DEFAULT_DEV_SQLITE = PROJECT_ROOT / "dev.db"
DEFAULT_DEV_SQLITE_URL = f"sqlite:///{DEFAULT_DEV_SQLITE}"


class BaseConfig:
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", "superseguro")
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", "dev-salt")
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("1", "true", "yes")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@codex.local")
    DATA_DIR = os.getenv("DATA_DIR", str(PROJECT_ROOT / "data"))
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
        "connect_args": {"check_same_thread": False}
        if str(SQLALCHEMY_DATABASE_URI).startswith("sqlite:///")
        else {},
    }
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
    AUTH_SIMPLE = os.getenv("AUTH_SIMPLE", "0").lower() in ("1", "true", "yes")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("1", "true", "yes")
    SESSION_COOKIE_SAMESITE = "Lax"


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", DEFAULT_DEV_SQLITE_URL)


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        **BaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        "connect_args": {"check_same_thread": False},
    }


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False


_CONFIG_MAP: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "dev": DevelopmentConfig,
    "testing": TestingConfig,
    "test": TestingConfig,
    "production": ProductionConfig,
    "prod": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(name: str | None = None) -> type[BaseConfig]:
    key = (
        name
        or os.getenv("CONFIG")
        or os.getenv("FLASK_ENV")
        or os.getenv("ENV")
        or "development"
    ).lower()
    return _CONFIG_MAP.get(key, DevelopmentConfig)


__all__ = [
    "get_config",
    "BaseConfig",
    "DevelopmentConfig",
    "TestingConfig",
    "ProductionConfig",
]
