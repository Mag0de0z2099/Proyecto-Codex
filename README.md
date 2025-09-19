# Proyecto-Codex

Servidor Flask para Codex Primera configuración


[![CI - Coverage](https://github.com/Mag0de0z2099/Proyecto-Codex/actions/workflows/ci-coverage.yml/badge.svg)](https://github.com/Mag0de0z2099/Proyecto-Codex/actions/workflows/ci-coverage.yml)
[![codecov](https://codecov.io/gh/Mag0de0z2099/Proyecto-Codex/branch/main/graph/badge.svg)](https://app.codecov.io/gh/Mag0de0z2099/Proyecto-Codex)
[![Render](https://img.shields.io/website?url=https%3A%2F%2Fproyecto-codex.onrender.com&label=Render%20Deploy&style=flat-square)](https://proyecto-codex.onrender.com)

## Checklist de despliegue seguro

Configura las variables de entorno **antes** de desplegar en Render u otra plataforma:

| Variable | Valor recomendado |
| --- | --- |
| `SECRET_KEY` | Cadena aleatoria de **32 bytes** o más. |
| `SECURITY_PASSWORD_SALT` | Cadena aleatoria dedicada para reset de contraseñas. |
| `DATABASE_URL` | URL de PostgreSQL gestionada (por ejemplo, `postgres://...`). |
| `FLASK_ENV` | `production` |
| `FLASK_DEBUG` | `0` |
| `SECURE_COOKIES` | `1` para forzar cookies seguras en HTTPS. |
| `LOG_LEVEL` | `INFO` (o `DEBUG` solo para diagnósticos puntuales). |

En producción la aplicación fuerza cookies `Secure`, `HttpOnly` y `SameSite=Lax`, protege los formularios con CSRF y aplica cabeceras de seguridad (CSP, HSTS, etc.).

## Operación

- **Gunicorn:** El Procfile y `render.yaml` inician el proyecto con `gunicorn -w 3 -t 60 app.main:app`.
- **Healthcheck:** `GET /healthz` devuelve `{"ok": true}` para liveness probes; `/api/v1/health` valida la conexión a la base.
- **Logging estructurado:** todos los logs van a `stdout` en JSON-like plano, incluyen `X-Request-ID` y respetan `LOG_LEVEL`.
- **Rate limiting:** `/auth/forgot-password` limita solicitudes a `5/minuto` y `30/hora` por IP.

Revisa los logs durante los primeros minutos tras cada deploy para detectar errores de integridad o restablecimientos de contraseña. Cada reset exitoso registra el `user_id` asociado (sin exponer el token).
