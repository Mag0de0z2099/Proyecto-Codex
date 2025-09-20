"""Entrada de referencia para tareas en segundo plano.

Este worker inicializa la aplicación Flask y mantiene un bucle de espera que
puedes reemplazar por la lógica de tu cola de tareas preferida (Celery, RQ,
Dramatiq, etc.).
"""

from __future__ import annotations

import logging
import os
import signal
import time
from types import FrameType

from app import create_app

# Flag global para terminar el bucle principal con señales SIGTERM/SIGINT.
_SHUTDOWN_REQUESTED = False


def _handle_shutdown(signum: int, frame: FrameType | None) -> None:
    """Marca que el worker debe apagarse de forma limpia."""

    global _SHUTDOWN_REQUESTED
    logging.getLogger(__name__).info("Recibida señal %s, iniciando apagado...", signum)
    _SHUTDOWN_REQUESTED = True


def main() -> int:
    """Punto de entrada del worker."""

    app = create_app()
    interval = int(os.getenv("WORKER_HEARTBEAT_INTERVAL", "30"))

    with app.app_context():
        logger = app.logger.getChild("worker")
        logger.info("Worker inicializado; heartbeat cada %s segundos", interval)

        signal.signal(signal.SIGTERM, _handle_shutdown)
        signal.signal(signal.SIGINT, _handle_shutdown)

        while not _SHUTDOWN_REQUESTED:
            logger.debug("Heartbeat del worker: en espera de tareas")
            time.sleep(interval)

        logger.info("Worker apagado correctamente")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
