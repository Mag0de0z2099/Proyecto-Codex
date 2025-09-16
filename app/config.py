"""Configuraciones para la aplicación Flask."""

from __future__ import annotations

import os
from typing import Type


class BaseConfig:
    """Configuración base compartida."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")


class DevConfig(BaseConfig):
    """Configuración para entornos de desarrollo."""

    DEBUG = True


class ProdConfig(BaseConfig):
    """Configuración para entornos de producción."""

    DEBUG = False


class TestConfig(BaseConfig):
    """Configuración para entornos de pruebas."""

    TESTING = True


def get_config(name: str | None) -> Type[BaseConfig]:
    """Obtener la clase de configuración según ``name``.

    Si no se especifica, se usa la variable de entorno ``FLASK_ENV`` y
    se asume producción por defecto.
    """

    env = (name or os.environ.get("FLASK_ENV") or "production").lower()
    if env.startswith("dev"):
        return DevConfig
    if env.startswith("test"):
        return TestConfig
    return ProdConfig
