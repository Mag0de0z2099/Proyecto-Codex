"""Blueprint con las rutas web del proyecto."""

from __future__ import annotations

from flask import Blueprint

bp_web = Blueprint("web", __name__)

from . import routes  # noqa: E402  (importa las rutas al registrar el blueprint)

__all__ = ["bp_web"]
