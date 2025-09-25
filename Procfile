# Proceso web principal (sirve la app Flask con Gunicorn)
web: gunicorn -w 3 -t 60 wsgi:app

release: flask db upgrade || true && flask seed-admin --email "$ADMIN_EMAIL" --password "$ADMIN_PASSWORD"

# Proceso de worker (ejemplo: tareas en segundo plano)
worker: python worker.py
