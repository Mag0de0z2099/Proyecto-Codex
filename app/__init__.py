"""Fábrica de la app Flask para Codex."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, g, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from typing import cast
from flask_login import AnonymousUserMixin
from pytz import timezone
from .config import get_config, load_config
from .errors import register_error_handlers
from .extensions import (
    csrf,
    db as extensions_db,
    init_auth_extensions,
    limiter,
    login_manager,
)
from .metrics import cleanup_multiprocess_directory
from .utils.scan_lock import get_scan_lock
from .migrate_ext import init_migrations
from .security_headers import set_security_headers
from .storage import ensure_dirs
from .registry import register_blueprints
from .telemetry import setup_logging
from .core.logging import init_logging
from .auth0 import init_auth0, requires_login


@login_manager.user_loader
def load_user(user_id: str):
    from app.models.user import User

    try:
        return User.query.get(int(user_id))
    except Exception:
        return None


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
    app.secret_key = os.getenv("SECRET_KEY")
    raw_uri = os.environ.get("DATABASE_URL", "")

    app.config.from_object(get_config())
    app.config.from_object(load_config(config_name))
    app.config.setdefault("LOG_LEVEL", "INFO")

    auth_disabled_env = os.getenv("AUTH_DISABLED")
    if auth_disabled_env is not None:
        app.config["AUTH_DISABLED"] = auth_disabled_env.strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
    else:
        app.config.setdefault("AUTH_DISABLED", False)

    from app.blueprints.archivos.helpers import (
        count_evidencias,
        evidencias_summary,
        human_size,
    )

    app.jinja_env.globals["count_evidencias"] = count_evidencias
    app.jinja_env.globals["evidencias_summary"] = evidencias_summary
    app.jinja_env.globals["human_size"] = human_size

    login_disabled_env = os.getenv("LOGIN_DISABLED")
    if login_disabled_env is not None:
        app.config["LOGIN_DISABLED"] = login_disabled_env.strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
    elif app.config.get("AUTH_DISABLED"):
        app.config["LOGIN_DISABLED"] = True
    elif app.config.get("TESTING"):
        app.config.setdefault("LOGIN_DISABLED", True)
    else:
        env_name = (os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "").lower()
        if env_name in {"dev", "development"}:
            app.config.setdefault("LOGIN_DISABLED", True)

    if app.config.get("AUTH_DISABLED") and not app.config.get("LOGIN_DISABLED"):
        app.config["LOGIN_DISABLED"] = True

    # ===== DEV MODE (apagado de seguridad por bandera) =====
    if os.getenv("DISABLE_SECURITY") == "1":
        app.config["SECURITY_DISABLED"] = True
        app.config["LOGIN_DISABLED"] = True        # @login_required no-op
        app.config["AUTH_DISABLED"] = True
        app.config["WTF_CSRF_ENABLED"] = False     # sin CSRF
        app.config["RATELIMIT_ENABLED"] = False    # sin rate limit
        app.config["JWT_COOKIE_CSRF_PROTECT"] = False

        # Usuario "siempre autenticado" para que plantillas/guards no fallen
        class DevUser(AnonymousUserMixin):
            id = 0
            email = "dev@local"
            username = "dev@local"
            role = "admin"
            is_admin = True

            @property
            def is_authenticated(self):
                return True

            @property
            def is_active(self):
                return True

            @property
            def is_anonymous(self):
                return False

        # Establecer usuario anónimo como DevUser (si existe login_manager)
        try:
            from app.extensions import login_manager

            login_manager.anonymous_user = DevUser
        except Exception:
            pass

        # CORS abierto (si está instalado flask-cors)
        try:
            from flask_cors import CORS

            CORS(app, supports_credentials=True)
        except Exception:
            pass

        # Carpeta de uploads (opcional)
        app.config.setdefault("UPLOAD_DIR", "/opt/render/project/data/uploads")
        try:
            import os as _os

            _os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)
        except Exception:
            pass
    # ===== FIN DEV MODE =====

    # Inicializa extensiones aquí (después de setear flags):
    try:
        from app.extensions import login_manager

        login_manager.init_app(app)
    except Exception:
        pass

    try:
        from app.extensions import csrf

        csrf.init_app(app)  # respetará WTF_CSRF_ENABLED=False en dev
    except Exception:
        pass

    if bool(app.config.get("LOGIN_DISABLED")):
        @app.before_request
        def _csrf_off_for_auth() -> None:
            from flask import request

            if request.path.startswith("/auth/"):
                setattr(request, "csrf_processing_exempt", True)

    app.jinja_env.globals["DEV_MODE"] = bool(
        app.config.get("AUTH_DISABLED")
        or app.config.get("SECURITY_DISABLED")
        or app.config.get("LOGIN_DISABLED")
    )

    try:
        # Limiter por IP
        app.limiter = cast(Limiter, limiter)
        app.limiter.key_func = get_remote_address
        limiter.init_app(app)
        if app.config.get("RATELIMIT_ENABLED") is False:
            setattr(app.limiter, "enabled", False)
    except Exception:
        pass

    configured_uri = str(app.config.get("SQLALCHEMY_DATABASE_URI", ""))
    uri = _normalize_db_url(raw_uri or configured_uri)
    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    if not app.config.get("SQLALCHEMY_TRACK_MODIFICATIONS"):
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.environ.get(
            "SECRET_KEY", "dev-secret-change-me"
        )
    app.config.setdefault(
        "ALLOW_SELF_SIGNUP",
        os.getenv("ALLOW_SELF_SIGNUP", "false").lower() in {"1", "true", "yes", "y"},
    )

    setup_logging(app)
    init_logging(app)

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
    extensions_db.init_app(app)
    init_migrations(app, extensions_db)
    init_auth_extensions(app)

    # Crear tablas nuevas automáticamente en DEV (sin molestar a Alembic)
    try:
        if app.config.get("SECURITY_DISABLED"):
            with app.app_context():
                extensions_db.create_all()
    except Exception:
        pass

    set_security_headers(app)

    register_error_handlers(app)

    # Inicializa Auth0
    init_auth0(app)

    @app.get("/me")
    @requires_login
    def me():
        from flask import session

        u = session.get("user") or {}
        return jsonify({
            "email": u.get("email"),
            "name": u.get("name"),
            "sub": u.get("sub"),
        })

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
            "pending_users_count": pending_count,
        }

    @app.context_processor
    def inject_config():
        return {"config": app.config}

    @app.context_processor
    def inject_dev_mode_flag():
        return {
            "DEV_MODE": bool(
                app.config.get("AUTH_DISABLED")
                or app.config.get("SECURITY_DISABLED")
                or app.config.get("LOGIN_DISABLED")
            )
        }

    # Blueprints
    from . import models  # noqa: F401

    blueprints = register_blueprints(app)

    from app.auth.routes import auth_bp

    if auth_bp.name not in app.blueprints:
        app.register_blueprint(auth_bp)

    from app.auth.reset import reset_bp

    if reset_bp.name not in app.blueprints:
        app.register_blueprint(reset_bp)

    from app.auth.totp import totp_bp

    if totp_bp.name not in app.blueprints:
        app.register_blueprint(totp_bp)

    if app.config.get("AUTH_DISABLED", False):
        try:
            from app.auth.diag import diag_bp

            if diag_bp.name not in app.blueprints:
                app.register_blueprint(diag_bp)
        except Exception:
            pass

    from app.blueprints.checklists.routes import bp as checklists_bp

    if checklists_bp.name not in app.blueprints:
        app.register_blueprint(checklists_bp)

    from app.blueprints.partes.routes import bp as partes_bp

    if partes_bp.name not in app.blueprints:
        app.register_blueprint(partes_bp)

    from app.agent.routes import agent_bp

    if agent_bp.name not in app.blueprints:
        app.register_blueprint(agent_bp)

    from app.dashboard.routes import dashboard_bp

    if dashboard_bp.name not in app.blueprints:
        app.register_blueprint(dashboard_bp)

    try:
        from app.blueprints.archivos.routes import bp as archivos_bp

        if archivos_bp.name not in app.blueprints:
            app.register_blueprint(archivos_bp)
    except Exception:
        pass

    env_name = (app.config.get("ENV") or "production").lower()
    if env_name not in {"prod", "production"}:
        try:
            from app.auth.dev import dev_bp
        except Exception:
            dev_bp = None
        else:
            if dev_bp and dev_bp.name not in app.blueprints:
                app.register_blueprint(dev_bp)

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

    from .commands import register_commands

    register_commands(app)

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

    from .cli.seed_admin import seed_admin as seed_admin_command

    if "seed-admin" not in app.cli.commands:
        app.cli.add_command(seed_admin_command)

    @app.errorhandler(Exception)
    def _unhandled_exception(exc: Exception):
        logging.exception("Unhandled | rid=%s", getattr(g, "request_id", "-"), exc_info=exc)
        rid = getattr(g, "request_id", "-")
        return (
            jsonify(
                {
                    "error": "internal_server_error",
                    "request_id": rid,
                    "path": request.path,
                }
            ),
            500,
        )

    return app


def __getattr__(name: str):
    if name == "db":
        return extensions_db
    raise AttributeError(name)


import sys as _sys

_sys.modules[__name__].db = extensions_db
