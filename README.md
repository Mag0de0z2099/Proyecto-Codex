# Proyecto Codex

Servidor Flask para Codex Primera configuración


## Autores
- Mag0de0z2099  
- Codex


[![CI - Coverage](https://github.com/Mag0de0z2099/Proyecto-Codex/actions/workflows/ci-coverage.yml/badge.svg)](https://github.com/Mag0de0z2099/Proyecto-Codex/actions/workflows/ci-coverage.yml)
[![codecov](https://codecov.io/gh/Mag0de0z2099/Proyecto-Codex/branch/main/graph/badge.svg)](https://codecov.io/gh/Mag0de0z2099/Proyecto-Codex)

<!-- Badges por flag (Codecov Pro) -->
[![api](https://codecov.io/gh/Mag0de0z2099/Proyecto-Codex/branch/main/graph/badge.svg?flag=api)](https://app.codecov.io/gh/Mag0de0z2099/Proyecto-Codex/flags/api)
[![auth](https://codecov.io/gh/Mag0de0z2099/Proyecto-Codex/branch/main/graph/badge.svg?flag=auth)](https://app.codecov.io/gh/Mag0de0z2099/Proyecto-Codex/flags/auth)
[![models](https://codecov.io/gh/Mag0de0z2099/Proyecto-Codex/branch/main/graph/badge.svg?flag=models)](https://app.codecov.io/gh/Mag0de0z2099/Proyecto-Codex/flags/models)
[![routes](https://codecov.io/gh/Mag0de0z2099/Proyecto-Codex/branch/main/graph/badge.svg?flag=routes)](https://app.codecov.io/gh/Mag0de0z2099/Proyecto-Codex/flags/routes)
[![services](https://codecov.io/gh/Mag0de0z2099/Proyecto-Codex/branch/main/graph/badge.svg?flag=services)](https://app.codecov.io/gh/Mag0de0z2099/Proyecto-Codex/flags/services)
[![utils](https://codecov.io/gh/Mag0de0z2099/Proyecto-Codex/branch/main/graph/badge.svg?flag=utils)](https://app.codecov.io/gh/Mag0de0z2099/Proyecto-Codex/flags/utils)
[![Render](https://img.shields.io/website?url=https%3A%2F%2Fproyecto-codex.onrender.com&label=Render%20Deploy&style=flat-square)](https://proyecto-codex.onrender.com)

## Deploy rápido

1. **Variables obligatorias**: define `DATABASE_URL` y `SECRET_KEY` antes de desplegar.
2. **Migración y seed**:

   ```bash
   alembic -c migrations/alembic.ini upgrade head
   FLASK_APP=app:create_app flask seed-admin --email admin@admin.com --password admin123
   ```

3. **Smoke tests**:

   ```bash
   curl -s https://tu-app.onrender.com/healthz
   curl -s -X POST https://tu-app.onrender.com/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@admin.com","password":"admin123"}'
   ```

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

> Nota: la aplicación usa `postgresql+psycopg://` (psycopg v3). No instales `psycopg2` ni `psycopg2-binary`; mantenemos `psycopg[binary]` en `requirements.txt`.

En producción la aplicación fuerza cookies `Secure`, `HttpOnly` y `SameSite=Lax`, protege los formularios con CSRF y aplica cabeceras de seguridad (CSP, HSTS, etc.).

> ℹ️ El seeding por defecto crea `admin@admin.com` / `admin123`.

Para usar otra clave, ejecutar:

```bash
FLASK_APP=app:create_app flask seed-admin --email admin@admin.com --password NUEVA_CLAVE
```

## Operación

- **Gunicorn:** El Procfile y `render.yaml` inician el proyecto con `gunicorn -w 3 -t 60 wsgi:app`.
- **Healthcheck:** `GET /healthz` devuelve `{"status": "ok"}` para liveness probes; `/api/v1/health` valida la conexión a la base.
- **Logging estructurado:** todos los logs van a `stdout` en JSON-like plano, incluyen `X-Request-ID` y respetan `LOG_LEVEL`.
- **Rate limiting:** `/auth/forgot-password` limita solicitudes a `5/minuto` y `30/hora` por IP.

Revisa los logs durante los primeros minutos tras cada deploy para detectar errores de integridad o restablecimientos de contraseña. Cada reset exitoso registra el `user_id` asociado (sin exponer el token).

## Procfile y procesos

El archivo `Procfile` describe los procesos que tu plataforma de despliegue debe iniciar. El repositorio incluye una versión extendida lista para producción y tareas en segundo plano:

```Procfile
# Proceso web principal (sirve la app Flask con Gunicorn)
web: gunicorn -w 3 -t 60 wsgi:app

# Proceso de worker (ejemplo: tareas en segundo plano)
worker: python worker.py
```

### `web`

- Atiende el tráfico HTTP usando Gunicorn.
- `-w 3` levanta tres workers; ajusta el número según el plan contratado o los núcleos disponibles.
- `-t 60` fija un timeout de 60 s para peticiones largas.
- `wsgi:app` apunta al objeto Flask creado en `wsgi.py`.

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

## Deploy rápido en Render

Variables necesarias:
- `DATABASE_URL` (cadena interna de Postgres con `?sslmode=require`)
- `SECRET_KEY` (cualquier cadena segura)

**Pre-deploy** corre migraciones y crea el admin:
```bash
alembic -c migrations/alembic.ini upgrade head && \
FLASK_APP=app:create_app flask seed-admin --email admin@admin.com --password admin123
```

### Endpoints de verificación
```bash
curl -s https://<tu-servicio>.onrender.com/healthz
curl -s -X POST https://<tu-servicio>.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@admin.com","password":"admin123"}'
```

## Autenticación JWT
```bash
BASE="https://<tu-servicio>.onrender.com"
LOGIN=$(curl -s -X POST "$BASE/api/v1/auth/login" -H "Content-Type: application/json" \
  -d '{"email":"admin@admin.com","password":"admin123"}')
TOKEN=$(python - <<'PY'
import json,sys; print(json.load(sys.stdin).get("access_token",""))
PY
<<<"$LOGIN")

# Ver perfil
curl -s "$BASE/api/v1/auth/me" -H "Authorization: Bearer $TOKEN"

# Listar pendientes (requiere admin)
curl -s "$BASE/api/v1/users?status=pending" -H "Authorization: Bearer $TOKEN"

### Refresh token
# Pide nuevos tokens usando el refresh recibido en /auth/login

### Listado con filtros, búsqueda y paginación
`GET /api/v1/users` acepta estos parámetros opcionales:

- `status`: `pending` o `approved`.
- `q`: fragmento del correo a buscar (no sensible a mayúsculas).
- `page`: número de página (por defecto 1).
- `per_page`: cantidad por página (por defecto 10, máximo 100).
REFRESH="<Pega_aquí_el_refresh_token>"
curl -s -X POST "$BASE/api/v1/auth/refresh" -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH\"}"

### Denylist y cierre de sesión
- `POST /api/v1/auth/logout`  \
  Revoca **ese** refresh (enviar como `Authorization: Bearer <refresh>` o body `{"refresh_token": "..."}`).

- `POST /api/v1/auth/logout_all` *(requiere access token)*  \
  Revoca **todos** los refresh del usuario (cierre de sesión global).

### Rate-limit de login
- Límite: **5 intentos por minuto por IP** (HTTP 429 al exceder).
```

## Mantenimiento (cron)

Comando para limpiar refresh expirados:

```bash
FLASK_APP=app:create_app flask cleanup-refresh --grace-days=0
```

En Render puedes crear un **cron job** (o servicio programado) que ejecute ese comando una vez al día (por ejemplo, 03:30 UTC).

## Telemetría (logs JSON)

- Configura el nivel con `LOG_LEVEL` (`INFO` por defecto).
- Los eventos clave (`login_ok`, `login_failed`, `login_not_approved`, `refresh_ok`, `refresh_revoked_or_expired`, `logout_ok`, `logout_all_ok`, `logout_missing_token`, `logout_invalid_refresh`) se emiten en JSON a stdout, listo para agregadores.
