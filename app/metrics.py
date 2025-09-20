from prometheus_client import Counter, Histogram, Gauge

# Resultados del escaneo
SCAN_CREATED = Counter("scan_created_total", "Archivos creados por escaneos", ["project"])
SCAN_UPDATED = Counter("scan_updated_total", "Archivos actualizados por escaneos", ["project"])
SCAN_SKIPPED = Counter("scan_skipped_total", "Archivos sin cambios por escaneos", ["project"])

# Ciclos y estado
SCAN_RUNS = Counter("scan_runs_total", "Ciclos de escaneo ejecutados", ["status"])
SCAN_DURATION = Histogram("scan_duration_seconds", "Duración del escaneo en segundos")
LOCK_CONTENTION = Counter("scan_lock_contention_total", "Veces que se saltó el escaneo por lock")

# Carpeta/proyecto registrados en DB
FOLDERS_REGISTERED = Gauge("folders_registered", "Folders registrados en DB")
ASSETS_REGISTERED = Gauge("assets_registered", "Assets registrados en DB")
