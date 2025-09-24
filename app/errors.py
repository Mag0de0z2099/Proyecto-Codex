from __future__ import annotations

import logging
import uuid

from flask import g, jsonify, request


def _json_error(status: int, message: str | None = None):
    return (
        jsonify(
            error={
                "code": status,
                "message": message or request.environ.get("werkzeug.exception", "error"),
                "path": request.path,
                "request_id": getattr(g, "request_id", None),
            }
        ),
        status,
    )


def register_instrumentation(app):
    @app.before_request
    def _assign_request_id():
        rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex
        g.request_id = rid

    @app.after_request
    def _attach_request_id(resp):
        rid = getattr(g, "request_id", None)
        if rid:
            resp.headers["X-Request-Id"] = rid
        return resp


def register_error_handlers(app):
    register_instrumentation(app)

    @app.errorhandler(400)
    def _400(e):  # pragma: no cover - message comes from Werkzeug
        return _json_error(400, getattr(e, "description", "Bad Request"))

    @app.errorhandler(401)
    def _401(e):
        return _json_error(401, getattr(e, "description", "Unauthorized"))

    @app.errorhandler(403)
    def _403(e):
        return _json_error(403, getattr(e, "description", "Forbidden"))

    @app.errorhandler(404)
    def _404(e):
        return _json_error(404, getattr(e, "description", "Not Found"))

    @app.errorhandler(405)
    def _405(e):
        return _json_error(405, getattr(e, "description", "Method Not Allowed"))

    @app.errorhandler(Exception)
    def _500(e):
        # log y respuesta JSON coherente
        try:
            app.logger.exception("Unhandled exception", exc_info=e)
        except Exception:
            logging.exception("Unhandled exception (fallback)")
        return _json_error(500, "Internal Server Error")
