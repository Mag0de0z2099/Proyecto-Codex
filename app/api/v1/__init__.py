from __future__ import annotations
from app.blueprints.api.v1 import bp_api_v1

bp = bp_api_v1

from . import ping, todos, users  # noqa: E402,F401
