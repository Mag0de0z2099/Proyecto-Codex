"""Feature flag helpers for security-related toggles."""

from __future__ import annotations

import os
from typing import Final

_FALSE_VALUES: Final[set[str]] = {"0", "false", "no", "off"}


def _is_truthy(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in _FALSE_VALUES


def is_feature_enabled(env_var: str, *, default: bool = True) -> bool:
    """Return True if the given environment flag is truthy."""

    return _is_truthy(os.getenv(env_var), default)


def is_2fa_enabled() -> bool:
    """Whether the MFA/TOTP flow should be enforced."""

    return is_feature_enabled("ENABLE_2FA", default=True)


__all__ = ["is_feature_enabled", "is_2fa_enabled"]
