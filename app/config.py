"""Configuraciones para la aplicación Flask."""

from __future__ import annotations

import os
from typing import Type


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*")
    TESTING = False
    DEBUG = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False


CONFIG_MAP: dict[str, Type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": BaseConfig,
}


def get_config(config_name: str | None = None) -> Type[BaseConfig]:
    """Obtiene una clase de configuración basada en el nombre o env."""
    if config_name:
        return CONFIG_MAP.get(config_name.lower(), BaseConfig)

    env_name = os.environ.get("FLASK_ENV") or os.environ.get("APP_ENV") or os.environ.get("ENV")
    if env_name:
        return CONFIG_MAP.get(env_name.lower(), BaseConfig)
    return BaseConfig
