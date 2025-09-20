from __future__ import annotations

from flask import Blueprint, render_template

public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def home():
    return render_template("index.html")
