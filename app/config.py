from __future__ import annotations

import os
from pathlib import Path


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
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
