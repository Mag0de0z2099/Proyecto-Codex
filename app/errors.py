"""Registro de manejadores de error para la aplicación."""

from __future__ import annotations

from typing import Any

from flask import Flask, jsonify, request


def _is_api_request() -> bool:
    """Determina si la solicitud apunta a la API."""
    path = request.path or ""
    return path.startswith("/api/")


def register_error_handlers(app: Flask) -> None:
    """Registra manejadores simples que devuelven texto o JSON."""

    @app.errorhandler(404)
    def not_found(error: Exception) -> tuple[Any, int]:  # pragma: no cover - decorador
        if app.debug:
            return ("Not Found", 404)
        if _is_api_request():
            return jsonify(error="Not Found"), 404
        return ("Not Found", 404)

    @app.errorhandler(400)
    def bad_request(error: Exception) -> tuple[Any, int]:  # pragma: no cover - decorador
        if _is_api_request():
            return jsonify(error="Bad Request"), 400
        return ("Bad Request", 400)

    @app.errorhandler(500)
    def server_error(error: Exception) -> tuple[Any, int]:  # pragma: no cover - decorador
        if _is_api_request():
            return jsonify(error="Server Error"), 500
        return ("Server Error", 500)
