#!/usr/bin/env bash
set -euo pipefail

# === Config =====
BRANCH="${BRANCH:-feature/ui-logo-siglo21}"
TITLE="${TITLE:-style(ui): refinar navbar y login con logo Siglo 21}"
BASE_BRANCH="${BASE_BRANCH:-main}"
REPO_URL="${REPO_URL:-}"   # ej: git@github.com:TU_USUARIO/TU_REPO.git o https://github.com/TU_USUARIO/TU_REPO.git

FILES=(
  "app/templates/base.html"
  "app/static/css/custom.css"
  "app/blueprints/auth/templates/auth/login.html"
)

# === Preflight ===
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "❌ No estás en un repo git"; exit 1; }

# Config mínima de autor si falta
if ! git config user.email >/dev/null; then
  git config user.email "ci@example.local"
fi
if ! git config user.name >/dev/null; then
  git config user.name "CI User"
fi

git fetch --all --prune || true

# Verificar remoto origin
if ! git remote get-url origin >/dev/null 2>&1; then
  if [[ -z "$REPO_URL" ]]; then
    echo "❌ No existe el remoto 'origin' y no se proporcionó REPO_URL."
    echo "   Soluciones:"
    echo "   - Añade el remoto manualmente: git remote add origin git@github.com:TU_USUARIO/TU_REPO.git"
    echo "   - O ejecuta: REPO_URL='<url>' ./create_pr_ui_logo.sh"
    exit 1
  else
    echo "ℹ️ Configurando remoto origin -> $REPO_URL"
    git remote add origin "$REPO_URL"
  fi
fi

# Asegurar base branch local
if git show-ref --verify --quiet "refs/heads/$BASE_BRANCH"; then
  git checkout "$BASE_BRANCH"
else
  # Intentar rastrear desde remoto si existe
  if git ls-remote --exit-code --heads origin "$BASE_BRANCH" >/dev/null 2>&1; then
    git checkout -b "$BASE_BRANCH" "origin/$BASE_BRANCH"
  else
    git checkout -b "$BASE_BRANCH"
  fi
fi

# Crear/actualizar rama de trabajo
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git checkout "$BRANCH"
else
  git checkout -b "$BRANCH" "$BASE_BRANCH"
fi

# Add files si existen
for f in "${FILES[@]}"; do
  if [[ -f "$f" ]]; then
    git add "$f"
  else
    echo "⚠️ Aviso: no encontré $f (continúo)."
  fi
done

# Commit si hay staged
if git diff --cached --quiet; then
  echo "ℹ️ No hay cambios nuevos para commitear; sigo con push."
else
  git commit -m "$TITLE

- Colocado el logo de Siglo 21 junto a 'SGC-Obra' en el encabezado.
- Refinados estilos de la barra de navegación y botones (alineación, hover, fondo translúcido).
- Envuelto el formulario de inicio de sesión en un contenedor centrado con encabezado claro.
- Forzada temporalmente la recarga del CSS para visualizar cambios inmediatos.
- Tests en verde (pytest)."
fi

# Push (crea upstream si no existe)
git push -u origin "$BRANCH"

# PR body
PR_BODY_FILE="$(mktemp)"
cat > "$PR_BODY_FILE" <<'MD'
## Resumen
Este PR mejora la interfaz de usuario en la barra de navegación y el formulario de login.

## Cambios principales
- **Encabezado (base.html)**
  - Se agregó el logo de **Siglo 21** junto a la marca “SGC-Obra”.
  - Estilos de navbar y botones refinados (alineación, hover, fondo translúcido).

- **Login (login.html)**
  - Formulario de autenticación centrado en un contenedor con encabezado claro.

- **CSS (custom.css)**
  - Reglas nuevas para navbar/botones y contenedor de login.
  - Recarga temporal del CSS desde `base.html` para visualizar cambios.

## Resultado esperado
- Header muestra el logo de **Siglo 21** junto al texto SGC-Obra.
- Navbar más clara y responsiva.
- Login centrado y legible.

## Testing
- ✅ `pytest` sin errores.
- ✅ Verificado visualmente en entorno local/staging.

## Screenshots
*(Agrega capturas si lo deseas)*
MD

# Crear PR si 'gh' está disponible
if command -v gh >/dev/null 2>&1; then
  gh pr create --base "$BASE_BRANCH" --head "$BRANCH" --title "$TITLE" --body-file "$PR_BODY_FILE"
  echo "✅ Pull Request creado con gh CLI."
else
  echo "ℹ️ No encontré 'gh'. Crea el PR manualmente en GitHub:"
  echo "   - Base: $BASE_BRANCH"
  echo "   - Head: $BRANCH"
  echo "   - Title: $TITLE"
  echo "   - Body: (usa el contenido de $PR_BODY_FILE)"
fi

echo "✨ Listo."
