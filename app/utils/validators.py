"""Validadores reutilizables para la aplicación."""

from __future__ import annotations

import re


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    """Valida que el email tenga un formato básico correcto."""

    return bool(_EMAIL_RE.match((email or "").strip()))
