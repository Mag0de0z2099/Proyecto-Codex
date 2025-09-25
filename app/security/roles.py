from functools import wraps
from flask import request, jsonify


def requires_role(required: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Simplificación para pruebas: rol en header
            role = request.headers.get("X-Role", "user")
            if role != required:
                return jsonify({"detail": "forbidden"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator
