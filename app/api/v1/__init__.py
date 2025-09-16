from __future__ import annotations
from flask import Blueprint

bp = Blueprint("api_v1", __name__)

from . import users  # noqa: E402,F401
