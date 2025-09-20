# Proceso web principal (sirve la app Flask con Gunicorn)
web: gunicorn -w 3 -t 60 app.main:app

# Proceso de worker (ejemplo: tareas en segundo plano)
worker: python worker.py
