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
        default_sqlite_path = PROJECT_ROOT / "instance" / "codex.db"
        default_sqlite_uri = f"sqlite:///{default_sqlite_path}"
        self.DATABASE_URL = os.getenv("DATABASE_URL", default_sqlite_uri)
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
        self.REMEMBER_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SECURE = True
        self.REMEMBER_COOKIE_SECURE = True
        self.SESSION_COOKIE_SAMESITE = "Lax"
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


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_FROM = os.getenv("MAIL_FROM", "no-reply@sgc.local")


class TestConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///test.db")


class DevConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dev.db")


class ProdConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")


def get_config():
    env = os.getenv("FLASK_ENV", "development").lower()
    if env in ("test", "testing"):
        return TestConfig
    if env.startswith("prod"):
        return ProdConfig
    return DevConfig


def load_config(env: str | None = None) -> Config:
    env_name = (env or os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "production").lower()

    if env is None and env_name in {"prod", "production"}:
        db_url_env = os.getenv("DATABASE_URL", "")
        running_ci = os.getenv("CI", "").lower() in {"true", "1"}
        if not running_ci and (not db_url_env or db_url_env.startswith("sqlite:")):
            env_name = "development"
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
