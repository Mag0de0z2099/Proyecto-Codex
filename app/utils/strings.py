"""Utility helpers for working with strings."""

from __future__ import annotations


def normalize_email(value: str | None) -> str | None:
    """Return the email in a canonical form.

    The function strips any leading or trailing whitespace and lowercases
    the value so that comparisons can be made consistently regardless of
    how the address was provided by the user.
    """

    if value is None:
        return None
    return value.strip().lower() or None
