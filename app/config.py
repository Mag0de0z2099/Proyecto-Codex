import os
from datetime import timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _list_env(name: str) -> list[str]:
    raw = os.getenv(name, "")
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _engine_options(uri: str) -> dict[str, object]:
    options: dict[str, object] = {"pool_pre_ping": True}
    if uri.startswith("sqlite:"):
        options["connect_args"] = {"check_same_thread": False}
    return options


class Config:
    APP_NAME = "Proyecto-Codex"
    TESTING = False
    DEBUG = False

    def __init__(self) -> None:
        self.SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
        self.SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", "dev-salt")
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///codex.db")
        self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SQLALCHEMY_ENGINE_OPTIONS = _engine_options(self.SQLALCHEMY_DATABASE_URI)
        self.RATELIMIT_STORAGE_URI = os.getenv(
            "RATELIMIT_STORAGE_URI", os.getenv("REDIS_URL", "memory://")
        )
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.DATA_DIR = os.getenv("DATA_DIR", str(PROJECT_ROOT / "data"))
        self.AUTH_SIMPLE = _bool_env("AUTH_SIMPLE", True)
        self.ALLOW_SELF_SIGNUP = _bool_env("ALLOW_SELF_SIGNUP", False)
        self.SIGNUP_MODE = os.getenv("SIGNUP_MODE", "invite")
        self.ALLOWLIST_DOMAINS = _list_env("ALLOWLIST_DOMAINS")
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SECURE = _bool_env("SESSION_COOKIE_SECURE")
        self.SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
        self.REMEMBER_COOKIE_DURATION = timedelta(
            seconds=int(os.getenv("REMEMBER_COOKIE_DURATION", "86400"))
        )
        self.FAKE_USERS = os.getenv("FAKE_USERS") == "1"
        self.FAKE_TODOS = os.getenv("FAKE_TODOS") == "1"
        self.FAKE_AUTH = os.getenv("FAKE_AUTH") == "1"
        self.APP_VERSION = os.getenv("APP_VERSION", "dev")
        self.GIT_SHA = os.getenv("GIT_SHA", "local")
        self.DEBUG = _bool_env("DEBUG", self.DEBUG)


class DevelopmentConfig(Config):
    DEBUG = True

    def __init__(self) -> None:
        super().__init__()
        self.DEBUG = True


class ProductionConfig(Config):
    DEBUG = False

    def __init__(self) -> None:
        super().__init__()
        self.DEBUG = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = False

    def __init__(self) -> None:
        super().__init__()
        self.DEBUG = False
        self.DATABASE_URL = "sqlite:///:memory:"
        self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL
        self.SQLALCHEMY_ENGINE_OPTIONS = _engine_options(self.SQLALCHEMY_DATABASE_URI)
        self.WTF_CSRF_ENABLED = False
        self.AUTH_SIMPLE = True


def load_config(env: str | None = None) -> Config:
    env_name = (env or os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "production").lower()
    if env_name in {"test", "testing"}:
        cfg: Config = TestingConfig()
    elif env_name in {"prod", "production"}:
        cfg = ProductionConfig()
    elif env_name in {"dev", "development"}:
        cfg = DevelopmentConfig()
    else:
        cfg = Config()

    cfg.SQLALCHEMY_DATABASE_URI = cfg.DATABASE_URL
    cfg.SQLALCHEMY_ENGINE_OPTIONS = _engine_options(cfg.SQLALCHEMY_DATABASE_URI)

    if (
        env_name in {"prod", "production"}
        and cfg.SQLALCHEMY_DATABASE_URI.startswith("sqlite:")
        and os.getenv("CI", "").lower() not in {"true", "1"}
    ):
        raise RuntimeError("DATABASE_URL no definido en producción (detectado sqlite)")

    return cfg
