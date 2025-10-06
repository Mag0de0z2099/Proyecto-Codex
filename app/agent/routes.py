"""Routes for quick environment audits."""

from __future__ import annotations

from flask import Blueprint, jsonify

from app.security.authz import require_login

from .env_audit import env_audit

agent_bp = Blueprint("agent", __name__, url_prefix="/agent")


@agent_bp.route("/env-audit")
@require_login
def env_a():
    return jsonify(env_audit())


__all__ = ["agent_bp"]
