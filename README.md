# Proyecto-Codex

Base Flask + gunicorn. Despliegue en **Render** con Auto-Deploy.  
CI con **pytest + coverage** y subida a **Codecov**.

[![CI - Coverage](https://github.com/TU_USUARIO/TU_REPO/actions/workflows/ci-coverage.yml/badge.svg)](https://github.com/TU_USUARIO/TU_REPO/actions/workflows/ci-coverage.yml)
[![codecov](https://codecov.io/gh/TU_USUARIO/TU_REPO/branch/main/graph/badge.svg)](https://app.codecov.io/gh/TU_USUARIO/TU_REPO)

## Ejecutar local
```bash
pip install -r requirements.txt
gunicorn -b 127.0.0.1:8000 app.main:app
```
