from __future__ import annotations

from flask import Blueprint, jsonify, render_template

bp_web = Blueprint(
    "web",
    __name__,
    template_folder="templates",
)


@bp_web.get("/")
def index():
    return render_template("home.html")


@bp_web.get("/health")
def health() -> str:
    return "ok"


@bp_web.get("/healthz")
def healthz():
    return jsonify(status="ok"), 200
