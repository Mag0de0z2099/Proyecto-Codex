import os

# Debug configurable: por defecto False
DEBUG = os.getenv("DEBUG", "False").lower() in ("1", "true", "yes")

# Secret key configurable desde entorno, con fallback
SECRET_KEY = os.getenv("SECRET_KEY", "superseguro")

# Ejemplo de configuración de base de datos (si aplica)
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")

# Seguridad extra opcional
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("1", "true", "yes")
SESSION_COOKIE_SAMESITE = "Lax"
