import time
import jwt
from flask import current_app

ALGO = "HS256"


def _secret() -> str:
    # Usa SECRET_KEY existente
    return current_app.config.get("SECRET_KEY", "dev-secret")


def encode_jwt(payload: dict, ttl_seconds: int = 3600) -> str:
    now = int(time.time())
    normalized = dict(payload)
    if "sub" in normalized and normalized["sub"] is not None:
        normalized["sub"] = str(normalized["sub"])
    to_encode = {
        "iat": now,
        "exp": now + ttl_seconds,
        **normalized,
    }
    return jwt.encode(to_encode, _secret(), algorithm=ALGO)


def decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, _secret(), algorithms=[ALGO])
    except Exception:
        return None
