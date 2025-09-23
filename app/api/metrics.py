from __future__ import annotations

import os

from flask import Blueprint, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY,
    generate_latest,
    multiprocess,
)

bp = Blueprint("metrics", __name__)


@bp.get("/metrics")
def metrics() -> Response:
    try:
        registry = None
        if os.getenv("PROMETHEUS_MULTIPROC_DIR"):
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)

        output = generate_latest(registry)
        if not output:
            output = generate_latest(REGISTRY)
        response = Response(output)
        response.headers["Content-Type"] = CONTENT_TYPE_LATEST
        return response  # pragma: no branch
    except Exception as exc:  # pragma: no cover - defensive fallback
        return Response(
            f"# metrics unavailable: {exc}\n",
            mimetype="text/plain",
            status=503,
        )
