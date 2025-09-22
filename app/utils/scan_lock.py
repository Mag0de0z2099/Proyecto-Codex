"""Helpers for obtaining the scanner lock across different backends."""

from __future__ import annotations

import os
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app import db
from app.metrics import scan_lock

from .lock import file_lock


def _is_postgres(engine: Engine) -> bool:
    """Return True when the SQLAlchemy engine is backed by PostgreSQL."""

    try:
        return (engine.dialect.name or "").startswith("postgres")
    except Exception:  # pragma: no cover - extremely defensive
        return False


@contextmanager
def advisory_lock_pg(key: int = 821_734):
    """Acquire a PostgreSQL advisory lock for the given key."""

    conn = db.engine.connect()
    try:
        got = conn.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": key}).scalar()
        if not got:
            raise TimeoutError("No pude obtener pg_advisory_lock")
        yield
    finally:
        try:
            conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": key})
        finally:
            conn.close()


@contextmanager
def get_scan_lock():
    """Return a context manager that provides the shared scanner lock."""

    timeout = int(os.getenv("SCAN_LOCK_TIMEOUT", "3"))
    key = int(os.getenv("SCAN_LOCK_KEY", "821734"))
    lock_file = os.getenv("SCAN_LOCK_FILE", "/tmp/sgc_scan.lock")

    if _is_postgres(db.engine):
        with scan_lock.track_inprogress():
            with advisory_lock_pg(key=key):
                yield
    else:
        with scan_lock.track_inprogress():
            with file_lock(lock_file, timeout=timeout):
                yield
