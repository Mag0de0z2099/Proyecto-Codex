"""Blueprint para el área administrativa del proyecto."""

from __future__ import annotations

from flask import Blueprint

bp_admin = Blueprint("admin", __name__)

from . import routes  # noqa: E402  (importa las rutas al registrar el blueprint)

__all__ = ["bp_admin"]
