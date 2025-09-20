#!/usr/bin/env bash
# Verifica métricas Prometheus del escáner end-to-end.
# - Crea proyecto y carpeta temporal con archivos
# - Levanta la app
# - Ejecuta scan-folder y scan-all
# - Valida que /metrics exponga series scan_*

set -euo pipefail

PORT="${PORT:-5000}"
HOST="127.0.0.1"
BASE_URL="http://${HOST}:${PORT}"
TMP_DIR="$(mktemp -d -t sgcscan-XXXX)"
DATA_DIR="${TMP_DIR}/dragado/bitacoras/semana_38"
PROJECT_NAME="Dragado 2025"

echo "🧪 Verificación de métricas — usando TMP_DIR=${TMP_DIR}"

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
step "Instalando dependencias (si falta algo)..."
pip install -q -r requirements.txt

# 1) Datos de prueba
step "Creando datos de prueba en ${DATA_DIR} ..."
mkdir -p "${DATA_DIR}"
echo "hola" > "${DATA_DIR}/informe.txt"

# 2) Arrancar la app (dev server)
step "Levantando Flask en ${BASE_URL} ..."
export FLASK_APP="app:create_app"
(flask run -p "${PORT}" >/dev/null 2>&1) &
sleep 1
retry_curl "${BASE_URL}/metrics" 30 0.5 || { echo "❌ No responde /metrics"; exit 1; }
echo "✅ /metrics responde"

# 3) Bootstrap mínimo de DB (crear proyecto si no existe)
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

# 4) Escanear carpeta temporal (scan-folder)
step "Ejecutando scan-folder (registra assets iniciales) ..."
flask scan-folder \
  --project "${PROJECT_NAME}" \
  --logical "bitacoras/2025/semana_38" \
  --root "${DATA_DIR}"

# 5) Confirmar métricas básicas (created/runs/duration)
step "Validando métricas tras scan-folder ..."
curl -s "${BASE_URL}/metrics" | grep -E "scan_(created|runs|duration)" | head || {
  echo "❌ No se encontraron series scan_created/runs/duration tras scan-folder"
  exit 1
}
echo "✅ Métricas iniciales presentes"

# 6) Re-escanear sin cambios (debería aumentar skipped)
step "Ejecutando scan-all (sin cambios) ..."
flask scan-all || true
curl -s "${BASE_URL}/metrics" | grep -E "scan_skipped_total" >/dev/null || {
  echo "❌ No se encontró scan_skipped_total tras scan-all sin cambios"
  exit 1
}
echo "✅ 'skipped' registrado"

# 7) Modificar archivo para provocar 'updated'
step "Modificando archivo para forzar 'updated' ..."
echo "cambio" >> "${DATA_DIR}/informe.txt"
flask scan-all
curl -s "${BASE_URL}/metrics" | grep -E "scan_updated_total" >/dev/null || {
  echo "❌ No se encontró scan_updated_total tras modificar y re-escanear"
  exit 1
}
echo "✅ 'updated' registrado"

# 8) Mostrar resumen útil
step "Resumen de métricas relevantes:"
curl -s "${BASE_URL}/metrics" | grep -E "scan_(created|updated|skipped|runs|duration|lock)|folders_registered|assets_registered" | sed -e 's/^/# /' | head -n 50

echo -e "\n✨ Todo OK: métricas Prometheus expuestas y activas en /metrics"
