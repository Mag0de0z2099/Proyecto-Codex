from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
INSTANCE_DIR = PROJECT_ROOT / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE = INSTANCE_DIR / "sgc.db"
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_SQLITE}"


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "superseguro")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT", "dev-salt")
    # Email opcional (si no se configura, se enviará a logs)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587 or 25))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@codex.local")
    # Directorio de datos persistente (Render)
    DATA_DIR = os.getenv("DATA_DIR", str(PROJECT_ROOT / "data"))
    # Construye la URI de SQLite si no hay DATABASE_URL (Postgres)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        DEFAULT_SQLITE_URL,
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Estabilidad de conexiones
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
        # Para SQLite multi-hilo bajo Gunicorn
        "connect_args": {"check_same_thread": False}
        if str(SQLALCHEMY_DATABASE_URI).startswith("sqlite:///")
        else {},
    }
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")


class DevConfig(BaseConfig):
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"


class ProdConfig(BaseConfig):
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        **BaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        "connect_args": {"check_same_thread": False},
    }


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
