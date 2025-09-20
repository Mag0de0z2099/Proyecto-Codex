# Proyecto Codex

[![CI - Tests](https://github.com/Mag0de0z2099/Proyecto-Codex/actions/workflows/ci.yml/badge.svg)](https://github.com/Mag0de0z2099/Proyecto-Codex/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/codecov/c/github/Mag0de0z2099/Proyecto-Codex?branch=main)](https://codecov.io/gh/Mag0de0z2099/Proyecto-Codex)
[![Deploy on Render](https://img.shields.io/badge/Render-Deployed-brightgreen)](https://dashboard.render.com/)
[![Heroku](https://img.shields.io/badge/Heroku-Ready-blueviolet)](https://www.heroku.com/)
[![Fly.io](https://img.shields.io/badge/Fly.io-Ready-8A2BE2)](https://fly.io/)

---


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

## Procfile y procesos

- **Procfile básico (`Procfile`):**

  ```
  web: gunicorn -w 3 -t 60 app.main:app
  ```

  - `web` es el proceso que recibirá tráfico HTTP.
  - `gunicorn -w 3` levanta 3 workers (ajusta según los recursos disponibles).
  - `-t 60` define un timeout de 60 s.
  - `app.main:app` apunta a la aplicación Flask principal (actualízalo si cambias el módulo).

  Render utiliza el mismo comando como “Start Command”; si lo eliminas en el panel, conservar el Procfile bastará para que lo detecte automáticamente.

- **Procfile extendido (opcional):**

  ```
  web: gunicorn -w 3 -t 60 app.main:app
  worker: python worker.py
  ```

  - Añade un proceso `worker` para ejecutar tareas en segundo plano (por ejemplo, colas con RQ/Celery, envíos de correos, etc.).
  - Render puede ignorar este proceso si no está configurado, pero si migras a plataformas que sí leen el Procfile (Heroku, Fly.io), podrás levantar web y worker sin cambios adicionales.

Documentar estos comandos en el repositorio evita dudas al desplegar en diferentes proveedores.
