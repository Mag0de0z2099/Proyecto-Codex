"""Routes for quick environment audits."""

from __future__ import annotations

from flask import Blueprint, jsonify
from flask_login import login_required

from .env_audit import env_audit

agent_bp = Blueprint("agent", __name__, url_prefix="/agent")


@agent_bp.get("/env-audit")
@login_required
def env_a():
    """Return the environment audit report as JSON."""

    return jsonify(env_audit())


__all__ = ["agent_bp"]
