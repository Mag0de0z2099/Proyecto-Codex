from __future__ import annotations
from flask import Blueprint

bp = Blueprint("web", __name__)

@bp.route("/")
def index():
    return "Hola desde Elyra + Render 🚀"
