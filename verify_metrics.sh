#!/usr/bin/env bash
# Verifica métricas Prometheus end-to-end.
# - Ejecuta migraciones Alembic (o fallback a db.create_all)
# - Crea datos de prueba
# - Levanta Flask
# - Ejecuta scan-folder / scan-all
# - Valida series scan_* en /metrics

set -euo pipefail

PORT="${PORT:-5000}"
HOST="127.0.0.1"
BASE_URL="http://${HOST}:${PORT}"
TMP_DIR="$(mktemp -d -t sgcscan-XXXX)"
DATA_DIR="${TMP_DIR}/dragado/bitacoras/semana_38"
PROJECT_NAME="Dragado 2025"

echo "🧪 Verificación de métricas — TMP_DIR=${TMP_DIR}"

cleanup() {
  set +e
  echo "🧹 Limpiando..."
  pkill -f "flask run -p ${PORT}" >/dev/null 2>&1 || true
  pkill -f "gunicorn .*:${PORT}" >/dev/null 2>&1 || true
  rm -rf "${TMP_DIR}" || true
}
trap cleanup EXIT

step() { echo -e "\n▶ $*"; }

retry_curl() {
  local url="$1" tries="${2:-20}" sleep_s="${3:-0.5}"
  for ((i=1; i<=tries; i++)); do
    if curl -sf "${url}" >/dev/null; then return 0; fi
    sleep "${sleep_s}"
  done
  return 1
}

# 0) Dependencias
step "Instalando dependencias..."
pip install -q -r requirements.txt

# 1) Migraciones (Postgres/SQLite)
step "Aplicando migraciones Alembic..."
export FLASK_APP="app:create_app"
set +e
alembic -c migrations/alembic.ini upgrade head
ALEMBIC_RC=$?
set -e
if [[ $ALEMBIC_RC -ne 0 ]]; then
  echo "⚠️ Alembic falló (entorno de dev o SQLite sin soporte); usando fallback db.create_all()"
  python - <<'PY'
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
    print("DB creada con create_all() (fallback temporal)")
PY
fi

# 2) Datos de prueba
step "Creando datos en ${DATA_DIR} ..."
mkdir -p "${DATA_DIR}"
echo "hola" > "${DATA_DIR}/informe.txt"

# 3) Arrancar la app
step "Levantando Flask en ${BASE_URL} ..."
(flask run -p "${PORT}" >/dev/null 2>&1) &
retry_curl "${BASE_URL}/metrics" 40 0.5 || { echo "❌ No responde /metrics"; exit 1; }
echo "✅ /metrics responde"

# 4) Crear proyecto si no existe
step "Creando proyecto '${PROJECT_NAME}' si no existe ..."
flask shell <<'PY'
from app.extensions import db
from app.models.project import Project
p = Project.query.filter_by(name="Dragado 2025").first()
if not p:
    p = Project(name="Dragado 2025")
    db.session.add(p); db.session.commit()

print("Proyecto listo:", p.id, p.name)
PY

# 5) Escaneo inicial
step "scan-folder (primer registro de assets)..."
flask scan-folder \
  --project "${PROJECT_NAME}" \
  --logical "bitacoras/2025/semana_38" \
  --root "${DATA_DIR}"

# 6) Validar métricas básicas
step "Validando métricas tras scan-folder ..."
curl -s "${BASE_URL}/metrics" | grep -E "scan_(created|runs|duration)" | head || {
  echo "❌ No se encontraron scan_created/runs/duration tras scan-folder"
  exit 1
}
echo "✅ Métricas iniciales presentes"

# 7) Re-escanear sin cambios (skipped)
step "scan-all (sin cambios) ..."
flask scan-all || true
curl -s "${BASE_URL}/metrics" | grep -E "scan_skipped_total" >/dev/null || {
  echo "❌ Falta scan_skipped_total tras scan-all sin cambios"
  exit 1
}
echo "✅ 'skipped' registrado"

# 8) Modificar archivo (updated)
step "Forzando 'updated' ..."
echo "cambio" >> "${DATA_DIR}/informe.txt"
flask scan-all
curl -s "${BASE_URL}/metrics" | grep -E "scan_updated_total" >/dev/null || {
  echo "❌ Falta scan_updated_total tras modificar y re-escanear"
  exit 1
}
echo "✅ 'updated' registrado"

# 9) Resumen
step "Resumen de métricas:"
curl -s "${BASE_URL}/metrics" | grep -E "scan_(created|updated|skipped|runs|duration|lock)|folders_registered|assets_registered" | sed -e 's/^/# /' | head -n 50

echo -e "\n✨ OK: métricas Prometheus activas en /metrics"
