"""Blueprint mínimo para un endpoint de salud sin dependencias."""

from __future__ import annotations

from flask import Blueprint, Response

bp_ping = Blueprint("ping", __name__)


@bp_ping.get("/ping")
def ping() -> Response:
    """Responde con un texto plano para los healthchecks externos."""
    return Response("pong", 200, {"Content-Type": "text/plain; charset=utf-8"})
