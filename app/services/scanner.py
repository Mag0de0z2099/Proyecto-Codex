"""Servicios para escanear carpetas y sincronizar assets."""

from __future__ import annotations

import os
import time
from typing import Dict, Tuple

from app.db import db
from app.metrics import (
    ASSETS_REGISTERED,
    FOLDERS_REGISTERED,
    SCAN_CREATED,
    SCAN_DURATION,
    SCAN_RUNS,
    SCAN_SKIPPED,
    SCAN_UPDATED,
)
from app.models import Project
from app.models.asset import Asset
from app.models.folder import Folder
from app.utils.files import guess_mime, sha256_of_file, split_root_rel


def scan_folder_record(folder: Folder) -> Tuple[int, int, int]:
    """Escanea una carpeta física asociada a ``folder`` y sincroniza sus assets."""

    created = updated = skipped = 0
    root = folder.fs_path
    if not root or not os.path.isdir(root):
        return (created, updated, skipped)

    for base, _, files in os.walk(root):
        for filename in files:
            full = os.path.join(base, filename)
            dir_rel, rel_filename = split_root_rel(full, root)
            rel_path = os.path.join(dir_rel, rel_filename) if dir_rel else rel_filename

            size = os.path.getsize(full)
            digest = sha256_of_file(full)
            mime = guess_mime(full)

            asset = Asset.query.filter_by(
                project_id=folder.project_id,
                folder_id=folder.id,
                relative_path=rel_path,
            ).first()
            if not asset:
                asset = Asset(
                    project_id=folder.project_id,
                    folder_id=folder.id,
                    filename=rel_filename,
                    relative_path=rel_path,
                    size_bytes=size,
                    sha256=digest,
                    mime_type=mime,
                    version=1,
                )
                db.session.add(asset)
                created += 1
            else:
                if asset.sha256 != digest or asset.size_bytes != size:
                    asset.sha256 = digest
                    asset.size_bytes = size
                    asset.mime_type = mime
                    asset.version = (asset.version or 1) + 1
                    updated += 1
                else:
                    skipped += 1

    db.session.commit()

    project: Project | None = getattr(folder, "project", None)
    project_label = project.name if project and project.name else "unknown"
    if created:
        SCAN_CREATED.labels(project_label).inc(created)
    if updated:
        SCAN_UPDATED.labels(project_label).inc(updated)
    if skipped:
        SCAN_SKIPPED.labels(project_label).inc(skipped)

    return (created, updated, skipped)


def scan_all_folders(limit: int | None = None) -> Dict[str, int]:
    """Escanea todas las carpetas registradas, opcionalmente limitando la cantidad."""

    query = Folder.query.order_by(Folder.id.asc())
    total_folders = query.count()
    if limit:
        query = query.limit(limit)

    totals: Dict[str, int] = {"created": 0, "updated": 0, "skipped": 0, "folders": 0}
    start = time.perf_counter()

    try:
        for folder in query.all():
            created, updated, skipped = scan_folder_record(folder)
            totals["created"] += created
            totals["updated"] += updated
            totals["skipped"] += skipped
            totals["folders"] += 1

        FOLDERS_REGISTERED.set(total_folders)
        ASSETS_REGISTERED.set(db.session.query(Asset).count())
    except Exception:
        SCAN_RUNS.labels("error").inc()
        raise
    else:
        SCAN_RUNS.labels("ok").inc()
        return totals
    finally:
        SCAN_DURATION.observe(time.perf_counter() - start)
