"""Manejadores de errores personalizados."""

from __future__ import annotations

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException


def _wants_json_response() -> bool:
    if request.path.startswith("/api/"):
        return True
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    if not best:
        return False
    json_q = request.accept_mimetypes["application/json"]
    html_q = request.accept_mimetypes["text/html"]
    return best == "application/json" and json_q >= html_q


def register_error_handlers(app: Flask) -> None:
    """Registrar manejadores de errores comunes."""

    def handle_http_error(error: HTTPException):
        if _wants_json_response():
            response = jsonify(error=getattr(error, "description", "error"))
            response.status_code = error.code or 500
            return response
        return error

    def handle_unexpected(error: Exception):
        app.logger.exception("Unhandled exception", exc_info=error)
        if _wants_json_response():
            response = jsonify(error="internal server error")
            response.status_code = 500
            return response
        raise error

    app.register_error_handler(HTTPException, handle_http_error)
    app.register_error_handler(Exception, handle_unexpected)
