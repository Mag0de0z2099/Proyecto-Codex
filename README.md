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

El archivo `Procfile` describe los procesos que tu plataforma de despliegue debe iniciar. El repositorio incluye una versión extendida lista para producción y tareas en segundo plano:

```Procfile
# Proceso web principal (sirve la app Flask con Gunicorn)
web: gunicorn -w 3 -t 60 app.main:app

# Proceso de worker (ejemplo: tareas en segundo plano)
worker: python worker.py
```

### `web`

- Atiende el tráfico HTTP usando Gunicorn.
- `-w 3` levanta tres workers; ajusta el número según el plan contratado o los núcleos disponibles.
- `-t 60` fija un timeout de 60 s para peticiones largas.
- `app.main:app` apunta al objeto Flask creado en `app/main.py`.

Render reutiliza este comando como *Start Command*; basta con mantener el `Procfile` en el repositorio para que lo detecte automáticamente.

### `worker`

- Es una referencia para ejecutar tareas en background (colas de Celery, RQ, Dramatiq o scripts personalizados).
- El archivo `worker.py` inicializa la app, escucha señales `SIGTERM/SIGINT` y emite un *heartbeat* cada 30 segundos; puedes modificar la lógica interna sin cambiar el comando del Procfile.
- Ajusta el intervalo con la variable `WORKER_HEARTBEAT_INTERVAL`.

### Escalado en diferentes plataformas

- **Render:** solo inicia el proceso `web` por defecto, pero conservar la definición del `worker` documenta que tu app está preparada para colas.
- **Heroku:** escala procesos con `heroku ps:scale web=1 worker=1`.
- **Fly.io:** replica el comportamiento con `fly scale count web=1 worker=1`.

### Ejecución local con Honcho

Honcho permite correr ambos procesos en tu máquina con una sola orden:

```bash
pip install honcho
honcho start
```

Verás un servicio levantando Gunicorn (`web`) y otro ejecutando `worker.py`. Esto resulta útil para probar integración con colas de mensajes antes de desplegar.

Documentar estos comandos en el repositorio evita dudas al desplegar en diferentes proveedores.
