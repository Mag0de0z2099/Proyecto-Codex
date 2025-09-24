from flask import Blueprint, jsonify, request, abort, current_app
import re
import os
from app.services import auth_service

bp = Blueprint("auth_v1", __name__, url_prefix="/api/v1/auth")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email:
        abort(400, description="Field 'email' is required.")
    if not _EMAIL_RE.match(email):
        abort(400, description="Invalid email format.")
    if not password or len(password) < 6:
        abort(400, description="Password must be at least 6 characters.")

    user = auth_service.verify_credentials(email=email, password=password, app=current_app)
    if not user:
        abort(401, description="Invalid credentials.")

    # Token falso para pruebas/CI (no JWT real)
    token = os.getenv("FAKE_JWT", "fake-jwt")
    return jsonify(ok=True, user=user, token=token), 200
