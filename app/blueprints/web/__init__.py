from __future__ import annotations

from flask import Blueprint, render_template

bp_web = Blueprint(
    "web",
    __name__,
    template_folder="templates",
)


@bp_web.get("/")
def index():
    return render_template("web/index.html")


@bp_web.get("/health")
def health() -> str:
    return "ok"
