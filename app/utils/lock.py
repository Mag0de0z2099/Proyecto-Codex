"""File-based lock utilities for cross-platform use."""

from __future__ import annotations

import contextlib
import os
import time

# Support Unix (fcntl) and Windows (msvcrt)
try:  # pragma: no cover - platform dependent import
    import fcntl

    _HAS_FCNTL = True
except Exception:  # pragma: no cover - Windows fallback
    _HAS_FCNTL = False
    import msvcrt


@contextlib.contextmanager
def file_lock(lock_path: str, timeout: int = 0):
    """Acquire a file-based lock with optional timeout.

    Args:
        lock_path: Destination path for the lock file.
        timeout: Seconds to keep trying to acquire the lock. If 0, try once.

    Raises:
        TimeoutError: If the lock cannot be acquired before the timeout expires.
    """

    directory = os.path.dirname(lock_path) or "."
    os.makedirs(directory, exist_ok=True)
    f = open(lock_path, "a+")
    start = time.time()

    def _try_lock() -> bool:
        if _HAS_FCNTL:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except BlockingIOError:
                return False
        else:  # pragma: no cover - Windows specific path
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                return True
            except OSError:
                return False

    acquired = _try_lock()
    while not acquired and timeout > 0 and (time.time() - start) < timeout:
        time.sleep(0.2)
        acquired = _try_lock()

    if not acquired:
        f.close()
        raise TimeoutError(f"No pude obtener lock: {lock_path}")

    try:
        # Write PID for diagnostics
        f.seek(0)
        f.truncate(0)
        f.write(str(os.getpid()))
        f.flush()
        yield
    finally:
        try:
            if _HAS_FCNTL:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            else:  # pragma: no cover - Windows specific path
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
        finally:
            f.close()


def get_scan_lock(timeout: int = 3):
    """Return a context manager to acquire the scan lock with default settings."""

    lock_path = os.getenv("SCAN_LOCK_FILE", "/tmp/sgc_scan.lock")
    return file_lock(lock_path, timeout=timeout)
