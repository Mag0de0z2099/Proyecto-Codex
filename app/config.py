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


class DevConfig(BaseConfig):
    DEBUG = True


class ProdConfig(BaseConfig):
    DEBUG = False


def get_config(name: str | None) -> type[BaseConfig]:
    env = name or os.environ.get("APP_ENV") or os.environ.get("FLASK_ENV") or "production"
    env = env.lower()
    if env in {"dev", "development"}:
        return DevConfig
    return ProdConfig
