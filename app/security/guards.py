from functools import wraps
from flask import current_app, request, jsonify, g
from .jwt import decode_jwt


def requires_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_app.config.get("SECURITY_DISABLED") or current_app.config.get(
            "LOGIN_DISABLED"
        ):
            return fn(*args, **kwargs)
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"detail": "unauthorized"}), 401
        token = auth.split(" ", 1)[1].strip()
        data = decode_jwt(token)
        if not data:
            return jsonify({"detail": "unauthorized"}), 401
        # Guardar contexto mínimo
        g.current_user_id = data.get("sub")
        g.current_user_role = data.get("role", "user")
        g.current_user_email = data.get("email")
        return fn(*args, **kwargs)

    return wrapper


def requires_role(required: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if current_app.config.get("SECURITY_DISABLED") or current_app.config.get(
                "LOGIN_DISABLED"
            ):
                return fn(*args, **kwargs)
            # Si ya pasó por requires_auth, usamos el rol del token
            role = getattr(g, "current_user_role", None)
            # Fallback para pruebas antiguas con X-Role
            if role is None:
                role = request.headers.get("X-Role", "user")
            if role != required:
                return jsonify({"detail": "forbidden"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator
