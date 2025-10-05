from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user

from app.models.user import User

auth_bp = Blueprint("auth", __name__, template_folder="../templates")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Credenciales inválidas", "danger")
            return render_template("auth/login.html")
        if not getattr(user, "is_active", True):
            flash("Usuario inactivo", "warning")
            return render_template("auth/login.html")
        login_user(user, remember=True)
        return redirect(url_for("dashboard_bp.index"))
    return render_template("auth/login.html")
