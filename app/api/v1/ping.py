from __future__ import annotations

from flask import jsonify

from . import bp


@bp.get("/ping")
def ping():
    return jsonify({"ok": True, "version": "v1"})
