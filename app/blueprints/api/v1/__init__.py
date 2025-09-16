"""Blueprint para la versión 1 de la API."""

from __future__ import annotations

from flask import Blueprint

bp_api_v1 = Blueprint("api_v1", __name__)

from . import routes  # noqa: E402  (importa las rutas al registrar el blueprint)
from . import todos  # noqa: E402  (importa endpoints CRUD)

__all__ = ["bp_api_v1"]
