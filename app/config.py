from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
INSTANCE_DIR = PROJECT_ROOT / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
def resolve_db_uri() -> str:
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url:
        if (
            "sslmode=" not in url
            and "localhost" not in url
            and "127.0.0.1" not in url
        ):
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}sslmode=require"
        return url
    return "sqlite:///dev.db"  # solo para desarrollo local


SQLALCHEMY_DATABASE_URI = resolve_db_uri()
SQLALCHEMY_ENGINE_OPTIONS: dict[str, object] = {"pool_pre_ping": True}
if SQLALCHEMY_DATABASE_URI.startswith("sqlite:"):
    SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {"check_same_thread": False}

RATELIMIT_STORAGE_URI = os.getenv("REDIS_URL", "memory://")

if (
    os.getenv("FLASK_ENV") == "production"
    and SQLALCHEMY_DATABASE_URI.startswith("sqlite:")
    and os.getenv("CI", "").lower() not in {"true", "1"}
):
    raise RuntimeError("DATABASE_URL no definido en producción (detectado sqlite)")

_RESOLVED_DB_URI = SQLALCHEMY_DATABASE_URI
_RATELIMIT_STORAGE_URI = RATELIMIT_STORAGE_URI


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
    SQLALCHEMY_DATABASE_URI = _RESOLVED_DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = dict(SQLALCHEMY_ENGINE_OPTIONS)
    RATELIMIT_STORAGE_URI = _RATELIMIT_STORAGE_URI
    AUTH_SIMPLE = os.getenv("AUTH_SIMPLE", "0").lower() in ("1", "true", "yes")
    SESSION_COOKIE_HTTPONLY = True
    _secure_cookies_flag = os.getenv("SECURE_COOKIES")
    SESSION_COOKIE_SECURE = (
        os.getenv("SESSION_COOKIE_SECURE", _secure_cookies_flag or "False")
        .lower()
        in ("1", "true", "yes")
    )
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    REMEMBER_COOKIE_DURATION = timedelta(
        seconds=int(os.getenv("REMEMBER_COOKIE_DURATION", "86400"))
    )
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class DevelopmentConfig(BaseConfig):
    DEBUG = True


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
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"


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
    "resolve_db_uri",
    "SQLALCHEMY_DATABASE_URI",
    "SQLALCHEMY_ENGINE_OPTIONS",
    "RATELIMIT_STORAGE_URI",
    "get_config",
    "BaseConfig",
    "DevelopmentConfig",
    "TestingConfig",
    "ProductionConfig",
]
