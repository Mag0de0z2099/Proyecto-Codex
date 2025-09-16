"""Rutas de la versión 1 de la API."""

from __future__ import annotations

from flask import jsonify

from . import bp_api_v1


@bp_api_v1.get("/ping")
def ping():
    """Responder con un mensaje de disponibilidad."""

    return jsonify(ok=True, version="v1"), 200
