#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-5000}"
BASE_URL="http://127.0.0.1:${PORT}"
PROJECT_NAME="Dragado 2025"
DATA_DIR="/tmp/dragado/bitacoras/semana_38"

echo "▶ Seed + Scan + Check para métricas"

export FLASK_APP=app:create_app

# Migraciones (por si corremos localmente)
set +e
alembic -c migrations/alembic.ini upgrade head
set -e || true

# Proyecto
flask shell <<'PY'
from app.extensions import db
from app.models.project import Project
p = Project.query.filter_by(name="Dragado 2025").first()
if not p:
    p = Project(name="Dragado 2025")
    db.session.add(p)
    db.session.commit()

print("Proyecto listo:", p.id, p.name)
PY

# Datos
mkdir -p "${DATA_DIR}"
echo "hola" > "${DATA_DIR}/informe.txt"

# Escaneo inicial (created)
flask scan-folder \
  --project "${PROJECT_NAME}" \
  --logical "bitacoras/2025/semana_38" \
  --root "${DATA_DIR}"

# Confirmar /metrics responde
curl -sf "${BASE_URL}/metrics" | head -n 10 >/dev/null || {
  echo "❌ /metrics no responde en ${BASE_URL}/metrics"
  exit 1
}

# Métricas básicas
echo "▶ Métricas tras scan-folder:"
curl -s "${BASE_URL}/metrics" | grep -E "scan_(created|runs|duration)" | head || true

# Re-escanear sin cambios (skipped)
flask scan-all
echo "▶ Métricas 'skipped':"
curl -s "${BASE_URL}/metrics" | grep -E "scan_skipped_total" || true

# Forzar 'updated'
echo "cambio" >> "${DATA_DIR}/informe.txt"
flask scan-all
echo "▶ Métricas 'updated':"
curl -s "${BASE_URL}/metrics" | grep -E "scan_updated_total" || true

echo "✅ Listo: revisa el dashboard o /metrics para ver las series."
