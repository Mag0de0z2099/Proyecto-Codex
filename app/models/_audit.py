"""Helper utilities to provide safe audit defaults in dev mode."""

from __future__ import annotations

from typing import Any

from flask_login import current_user


def fallback_user_id() -> int:
    """Return a safe user id for audit fields when security is disabled."""

    try:
        user: Any = current_user  # type: ignore[assignment]
        return int(getattr(user, "id", 0) or 0)
    except Exception:  # pragma: no cover - defensive
        return 0
