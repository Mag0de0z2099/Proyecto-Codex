release: set -euxo pipefail; python -m alembic -c migrations/alembic.ini upgrade head; python -m flask --app app:create_app seed-admin --email "${ADMIN_EMAIL:-admin@admin.com}" --password "${ADMIN_PASSWORD:-admin123}"

# Proceso de worker (ejemplo: tareas en segundo plano)
worker: python worker.py
