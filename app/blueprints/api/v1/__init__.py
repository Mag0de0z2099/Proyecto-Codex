"""Versión 1 de la API pública."""

from __future__ import annotations

from flask import Blueprint, Response, jsonify

bp_api_v1 = Blueprint("api_v1", __name__)


@bp_api_v1.route("/ping")
def ping() -> tuple[Response, int]:
    """Devuelve un mensaje mínimo para verificar disponibilidad."""
    return jsonify(message="pong"), 200
