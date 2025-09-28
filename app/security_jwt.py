"""Compatibilidad con flask-jwt-extended en modo DEV.

Este módulo expone ``jwt_required`` de forma perezosa para que, cuando la
bandera ``DISABLE_SECURITY=1`` esté activa, cualquier decoración con
``@jwt_required`` se convierta en un no-op. En otros entornos simplemente se
reexporta el decorador real desde ``flask_jwt_extended``.
"""

from __future__ import annotations

import os


if os.getenv("DISABLE_SECURITY") == "1":

    def jwt_required(*_args, **_kwargs):  # type: ignore[unused-argument]
        def decorator(fn):
            return fn

        return decorator


else:  # pragma: no cover - import opcional
    from flask_jwt_extended import jwt_required  # type: ignore[misc]  # noqa: F401


__all__ = ["jwt_required"]
