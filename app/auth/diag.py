from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash

from app.models.user import User


diag_bp = Blueprint("auth_diag", __name__, url_prefix="/auth")


@diag_bp.route("/diag", methods=["POST"])
def diag():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    user = User.query.filter_by(email=email).first()
    return jsonify(
        {
            "user_exists": bool(user),
            "pwd_ok": bool(user and check_password_hash(user.password_hash, password)),
            "failed_logins": getattr(user, "failed_logins", None),
            "lock_until": getattr(user, "lock_until", None),
        }
    )
