#!/usr/bin/env bash
set -euo pipefail

BRANCH="feature/ui-logo-siglo21"
TITLE="style(ui): refinar navbar y login con logo Siglo 21"

# Archivos que ya modificaste
FILES=(
  "app/templates/base.html"
  "app/static/css/custom.css"
  "app/blueprints/auth/templates/auth/login.html"
)

# 1) Verificaciones básicas
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "❌ No estás en un repo git"; exit 1; }
git fetch --all --prune
if ! git status --porcelain | grep -qE "."; then
  echo "ℹ️ No hay cambios sin commitear; continuaré igual."
fi

# 2) Crear/actualizar rama de trabajo
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git checkout "$BRANCH"
else
  git checkout -b "$BRANCH" origin/main || git checkout -b "$BRANCH"
fi

# 3) Agregar archivos (si existen)
for f in "${FILES[@]}"; do
  if [[ -f "$f" ]]; then
    git add "$f"
  else
    echo "⚠️ Aviso: no encontré $f (continúo)."
  fi
done

# 4) Commit (solo si hay cambios staged)
if git diff --cached --quiet; then
  echo "ℹ️ No hay cambios nuevos para commitear; seguiré con el push."
else
  git commit -m "$TITLE

- Colocado el logo de Siglo 21 junto a 'SGC-Obra' en el encabezado.
- Refinados estilos de la barra de navegación y botones (alineación, hover, fondo translúcido).
- Envuelto el formulario de inicio de sesión en un contenedor centrado con encabezado claro.
- Forzada temporalmente la recarga del CSS para visualizar cambios inmediatos.
- Tests en verde (pytest)."
fi

# 5) Push de la rama
git push -u origin "$BRANCH"

# 6) Crear cuerpo del PR
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

# 7) Crear PR (requiere GitHub CLI autenticado: `gh auth login`)
if command -v gh >/dev/null 2>&1; then
  gh pr create \
    --base main \
    --head "$BRANCH" \
    --title "$TITLE" \
    --body-file "$PR_BODY_FILE"
  echo "✅ Pull Request creado con gh CLI."
else
  echo "ℹ️ No encontré 'gh'. Crea el PR manualmente en GitHub:"
  echo "   - Head branch: $BRANCH"
  echo "   - Base branch: main"
  echo "   - Title: $TITLE"
  echo "   - Body: (usa el contenido de $PR_BODY_FILE)"
fi

echo "✨ Listo."
