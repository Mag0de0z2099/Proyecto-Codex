"""Security helpers for Flask responses."""

from __future__ import annotations

from flask import Flask


def set_security_headers(app: Flask) -> None:
    """Register an ``after_request`` hook that injects security headers."""

    @app.after_request  # type: ignore[misc]
    def _headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        resp.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        resp.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=63072000; includeSubDomains; preload",
        )
        resp.headers.setdefault("Content-Security-Policy", "default-src 'self'")
        return resp

