"""Fábrica de la app Flask para Codex."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_login import AnonymousUserMixin
from pytz import timezone
from .cli_sync import register_sync_cli
from .config import load_config
from .errors import register_error_handlers
from .extensions import csrf, db, init_auth_extensions, limiter
from .metrics import cleanup_multiprocess_directory
from .utils.scan_lock import get_scan_lock
from .cli import register_cli
from .migrate_ext import init_migrations
from .security_headers import set_security_headers
from .storage import ensure_dirs
from .registry import register_blueprints
from .telemetry import setup_logging


def _normalize_db_url(raw: str | None) -> str:
    """
    Normaliza la DATABASE_URL para evitar errores:
    - Convierte postgres:// -> postgresql+psycopg://
    - Si es SQLite, elimina cualquier query (?sslmode=...)
    - Si es Postgres, asegura sslmode=require (si no está presente)
    """

    if not raw:
        return "sqlite:///dev.db"

    if raw.startswith("postgres://"):
        raw = raw.replace("postgres://", "postgresql+psycopg://", 1)
    elif raw.startswith("postgresql://"):
        raw = raw.replace("postgresql://", "postgresql+psycopg://", 1)

    parts = urlsplit(raw)
    scheme = parts.scheme

    if scheme.startswith("sqlite"):
        base = raw.split("?", 1)[0]
        base = base.split("#", 1)[0]
        fragment = f"#{parts.fragment}" if parts.fragment else ""
        return f"{base}{fragment}"

    if scheme.startswith("postgresql"):
        query_params = dict(parse_qsl(parts.query))
        query_params.setdefault("sslmode", "require")
        return urlunsplit(
            (
                scheme,
                parts.netloc,
                parts.path,
                urlencode(query_params),
                parts.fragment,
            )
        )

    return raw


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    raw_uri = os.environ.get("DATABASE_URL", "")

    app.config.from_object(load_config(config_name))
    app.config.setdefault("LOG_LEVEL", "INFO")

    # === MODO DEV: apaga seguridad si DISABLE_SECURITY=1 ===
    if os.getenv("DISABLE_SECURITY") == "1":
        app.config["LOGIN_DISABLED"] = True
        app.config["WTF_CSRF_ENABLED"] = False

        class DevUser(AnonymousUserMixin):
            @property
            def is_authenticated(self):
                return True

            @property
            def is_active(self):
                return True

            @property
            def is_anonymous(self):
                return False

            id = 0
            email = "dev@local"
            username = "dev@local"
            role = "admin"
            is_admin = True

        from app.extensions import login_manager

        login_manager.anonymous_user = DevUser

        try:
            limiter.enabled = False
        except Exception:
            pass
    # === fin MODO DEV ===

    configured_uri = str(app.config.get("SQLALCHEMY_DATABASE_URI", ""))
    uri = _normalize_db_url(raw_uri or configured_uri)
    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    if not app.config.get("SQLALCHEMY_TRACK_MODIFICATIONS"):
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me")
    app.config.setdefault(
        "ALLOW_SELF_SIGNUP",
        os.getenv("ALLOW_SELF_SIGNUP", "false").lower() in {"1", "true", "yes", "y"},
    )

    setup_logging(app)

    # DEBUG: imprime la URI y, si es SQLite, la ruta absoluta del archivo
    try:
        effective_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        print(f"DB URI -> {effective_uri}")
        if effective_uri.startswith("sqlite:///"):
            sqlite_path = Path(effective_uri.replace("sqlite:///", "", 1)).expanduser().resolve()
            print(f"[DEBUG] SQLite file -> {sqlite_path}")
    except Exception as exc:  # pragma: no cover - logging auxiliar
        print(f"[DEBUG] No se pudo imprimir DB info: {exc}")

    # Asegura DATA_DIR y muestra la URI (útil en logs de Render)
    data_dir = Path(app.config["DATA_DIR"])
    data_dir.mkdir(parents=True, exist_ok=True)

    db_uri = str(app.config.get("SQLALCHEMY_DATABASE_URI", ""))
    app.logger.info("DB URI -> %s", db_uri)
    if db_uri.startswith("sqlite:///") and not db_uri.endswith(":memory:"):
        sqlite_path = Path(db_uri.replace("sqlite:///", "", 1)).expanduser().resolve()
        app.logger.info("[DEBUG] SQLite file -> %s", sqlite_path)

    # Directorios persistentes (DATA_DIR, instance/, etc.)
    ensure_dirs(app)

    upload_root = os.environ.get("UPLOAD_FOLDER") or os.path.join(
        os.environ.get("DATA_DIR", str(app.config.get("DATA_DIR", "/data"))),
        "uploads",
        "checklists",
    )
    Path(upload_root).mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_CHECKLISTS_DIR"] = upload_root
    if os.getenv("PROMETHEUS_MULTIPROC_CLEAN_ON_START", "0").lower() in (
        "1",
        "true",
        "yes",
    ):
        cleanup_multiprocess_directory()

    # DB y extensiones compartidas
    db.init_app(app)
    init_migrations(app, db)
    init_auth_extensions(app)
    if os.getenv("DISABLE_SECURITY") != "1":
        limiter.init_app(app)

    set_security_headers(app)

    register_error_handlers(app)

    # Variables globales seguras para Jinja (evita usar `current_app` en plantillas)
    @app.context_processor
    def inject_globals():
        try:
            view_functions = app.view_functions
            has_web_index = "web.index" in view_functions
            has_web_upload = "web.upload" in view_functions
        except Exception:
            has_web_index = False
            has_web_upload = False
        try:
            from app.models import User as _User  # import local para evitar ciclos

            pending_count = _User.query.filter(_User.status == "pending").count()
        except Exception:
            pending_count = 0
        return {
            "has_web_index": has_web_index,
            "has_web_upload": has_web_upload,
            "config": app.config,
            "pending_users_count": pending_count,
        }

    # Blueprints
    from . import models  # noqa: F401

    blueprints = register_blueprints(app)

    # Registro de blueprints existentes
    try:
        from .routes.health import bp as health_bp

        app.register_blueprint(health_bp)
    except Exception:
        # Evita romper si el import difiere durante refactors
        pass

    try:
        from .routes.auth import bp as auth_bp

        app.register_blueprint(auth_bp)
    except Exception:
        pass

    try:
        from app.blueprints.checklists import bp as cl_bp

        app.register_blueprint(cl_bp)
    except Exception:
        pass

    from app.blueprints.partes import bp as partes_bp

    app.register_blueprint(partes_bp)

    from app.blueprints.dashboard import bp as dashboard_bp

    app.register_blueprint(dashboard_bp)

    # Exentamos la API pública JSON del CSRF global
    api_v1_bp = blueprints.get("api_v1")
    if api_v1_bp is not None:
        csrf.exempt(api_v1_bp)

    auth_api_bp = blueprints.get("auth_api")
    if auth_api_bp is not None:
        csrf.exempt(auth_api_bp)

    ping_bp = blueprints.get("ping")
    if ping_bp is not None:
        limiter.exempt(ping_bp)

    register_cli(app)
    register_sync_cli(app)

    if os.getenv("SCHEDULER_ENABLED", "0") == "1":
        from app.services.scanner import scan_all_folders

        tz_name = os.getenv("APP_TZ", "America/Monterrey")
        try:
            tz = timezone(tz_name)
        except Exception:  # pragma: no cover - defensive fallback
            tz = timezone("UTC")
            app.logger.warning(
                "APP_TZ inválida '%s', usando UTC como valor por defecto.", tz_name
            )

        try:
            interval_min = int(os.getenv("SCAN_INTERVAL_MIN", "15"))
        except ValueError:  # pragma: no cover - defensive fallback
            interval_min = 15
            app.logger.warning(
                "SCAN_INTERVAL_MIN inválido, usando 15 minutos por defecto."
            )

        scheduler = BackgroundScheduler(timezone=tz)

        def job() -> None:
            with app.app_context():
                try:
                    with get_scan_lock():
                        stats = scan_all_folders()
                        app.logger.info("[scanner] %s", stats)
                except TimeoutError:
                    app.logger.info("[scanner] saltado: lock ocupado.")

        scheduler.add_job(
            job,
            "interval",
            minutes=interval_min,
            id="scan_all_folders",
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()
        app.extensions.setdefault("apscheduler", scheduler)
        app.logger.info("Scheduler ON cada %s min (TZ=%s)", interval_min, tz)

    secret_key = app.config.get("SECRET_KEY", "")
    if not secret_key or len(secret_key) < 32:
        app.logger.warning(
            "SECRET_KEY is shorter than 32 characters. Provide a secure 32+ byte key for production.",
        )

    return app
