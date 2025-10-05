"""Simple environment configuration audit helpers."""

from __future__ import annotations

import os


def env_audit() -> dict[str, object]:
    """Return a quick assessment of critical environment variables."""

    issues: list[str] = []
    secret_key = os.getenv("SECRET_KEY", "")
    if not secret_key or len(secret_key) < 24:
        issues.append("SECRET_KEY débil o ausente")

    database_url = os.getenv("DATABASE_URL", "")
    if database_url and not database_url.startswith("postgresql"):
        issues.append("DATABASE_URL no apunta a Postgres en producción")

    return {"ok": not issues, "issues": issues}


__all__ = ["env_audit"]
