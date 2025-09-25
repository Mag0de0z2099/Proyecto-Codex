import time
import uuid

import jwt
from flask import current_app

ALGO = "HS256"


def _secret() -> str:
    # Usa SECRET_KEY existente
    return current_app.config.get("SECRET_KEY", "dev-secret")


def encode_jwt(payload: dict, ttl_seconds: int = 3600, typ: str = "access") -> str:
    now = int(time.time())
    normalized = dict(payload)
    if "sub" in normalized and normalized["sub"] is not None:
        normalized["sub"] = str(normalized["sub"])
    to_encode = {
        "iat": now,
        "exp": now + ttl_seconds,
        "typ": typ,
        **normalized,
    }
    return jwt.encode(to_encode, _secret(), algorithm=ALGO)


def decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, _secret(), algorithms=[ALGO])
    except Exception:
        return None


def gen_jti() -> str:
    return uuid.uuid4().hex


def encode_refresh_jwt(
    payload: dict, ttl_seconds: int = 7 * 24 * 3600, jti: str | None = None
) -> str:
    token_jti = jti or gen_jti()
    return encode_jwt({**payload, "jti": token_jti}, ttl_seconds=ttl_seconds, typ="refresh")
