"""Compat wrapper to disable JWT requirements when DISABLE_SECURITY=1."""

from __future__ import annotations

import os
from typing import Any, Callable

F = Callable[..., Any]


if os.getenv("DISABLE_SECURITY") == "1":

    def jwt_required(*args: Any, **kwargs: Any):  # type: ignore[unused-ignore]
        def decorator(fn: F) -> F:
            return fn

        return decorator

else:  # pragma: no cover - depende de la extensión opcional
    try:
        from flask_jwt_extended import jwt_required  # type: ignore
    except Exception:

        def jwt_required(*args: Any, **kwargs: Any):  # type: ignore[unused-ignore]
            def decorator(fn: F) -> F:
                return fn

            return decorator
