"""Inicialización de extensiones y hooks personalizados."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from flask import Flask, request


def _coerce_origins(raw: object) -> Sequence[str]:
    if raw is None:
        return ("*",)
    if isinstance(raw, str):
        parts = [item.strip() for item in raw.split(",")]
        return tuple(part for part in parts if part)
    if isinstance(raw, Iterable):
        cleaned: list[str] = []
        for item in raw:
            text = str(item).strip()
            if text:
                cleaned.append(text)
        return tuple(cleaned) or ("*",)
    return (str(raw),)


def init_extensions(app: Flask) -> None:
    """Configurar extensiones y middleware para la aplicación."""

    origins = _coerce_origins(app.config.get("ALLOWED_ORIGINS", "*"))

    @app.after_request
    def apply_cors_headers(response):
        origin = request.headers.get("Origin")
        allow_origin = "*"
        if origins and "*" not in origins:
            if origin and origin in origins:
                allow_origin = origin
            else:
                allow_origin = origins[0]
        response.headers.setdefault("Access-Control-Allow-Origin", allow_origin)
        response.headers.setdefault(
            "Access-Control-Allow-Headers", "Content-Type, Authorization"
        )
        response.headers.setdefault(
            "Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        )
        response.headers.setdefault("Access-Control-Allow-Credentials", "true")
        if response.headers.get("Access-Control-Allow-Origin") != "*":
            vary_header = response.headers.get("Vary")
            if vary_header:
                vary_values = {value.strip() for value in vary_header.split(",") if value.strip()}
                if "Origin" not in vary_values:
                    vary_values.add("Origin")
                    response.headers["Vary"] = ", ".join(sorted(vary_values))
            else:
                response.headers["Vary"] = "Origin"
        return response

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            return app.make_default_options_response()
        return None
