"""Configuración compartida para las pruebas."""

from __future__ import annotations

import sys
from pathlib import Path

# Aseguramos que la raíz del proyecto esté en sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
