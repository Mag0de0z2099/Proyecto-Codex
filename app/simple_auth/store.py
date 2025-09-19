from __future__ import annotations

import json
import threading
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

_lock = threading.Lock()


def _store_path(app):
    base = app.config.get("DATA_DIR") or app.instance_path
    Path(base).mkdir(parents=True, exist_ok=True)
    return Path(base) / "simple_users.json"


def _load(app):
    p = _store_path(app)
    if not p.exists():
        return {}
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(app, data):
    p = _store_path(app)
    tmp = p.with_suffix(".tmp")
    with _lock:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(p)


def ensure_bootstrap_admin(app):
    data = _load(app)
    if "admin" not in data:
        data["admin"] = {
            "pw": generate_password_hash("admin"),
            "is_admin": True,
            "is_active": True,
        }
        _save(app, data)


def add_user(app, username: str, password: str, is_admin: bool = False):
    username = (username or "").strip()
    if not username or not password:
        raise ValueError("Usuario y contraseña son requeridos.")
    data = _load(app)
    if username in data:
        raise ValueError("Ese usuario ya existe.")
    data[username] = {
        "pw": generate_password_hash(password),
        "is_admin": bool(is_admin),
        "is_active": True,
    }
    _save(app, data)


def verify(app, username: str, password: str):
    data = _load(app)
    u = data.get((username or "").strip())
    if not u or not u.get("is_active", True):
        return None
    if not check_password_hash(u["pw"], password):
        return None
    return {"username": username, "is_admin": bool(u.get("is_admin")), "is_active": True}


def list_users(app):
    data = _load(app)
    return [
        {
            "username": k,
            "is_admin": bool(v.get("is_admin")),
            "is_active": bool(v.get("is_active", True)),
        }
        for k, v in data.items()
    ]
