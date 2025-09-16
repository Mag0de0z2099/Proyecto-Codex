import os


def _clean(p: str) -> str:
    return os.path.abspath(os.path.expanduser(p))


def get_data_dir(app) -> str:
    base = app.config.get("DATA_DIR") or os.environ.get("DATA_DIR") or "./data"
    return _clean(base)


def ensure_dirs(app) -> str:
    base = get_data_dir(app)
    # Crea subdirectorios típicos
    for sub in ("uploads", "db"):
        os.makedirs(os.path.join(base, sub), exist_ok=True)
    app.logger.info("DATA_DIR=%s", base)
    return base


def join(app, *parts) -> str:
    return os.path.join(get_data_dir(app), *parts)
