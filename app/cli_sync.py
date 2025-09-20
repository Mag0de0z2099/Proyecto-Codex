from __future__ import annotations

import os

import click

from app.db import db
from app.models.asset import Asset
from app.models.folder import Folder
from app.models import Project
from app.utils.files import guess_mime, sha256_of_file, split_root_rel


def register_sync_cli(app):
    @app.cli.command("scan-folder")
    @click.option(
        "--project",
        "project_name",
        required=True,
        help="Nombre del proyecto (de la tabla projects.name)",
    )
    @click.option(
        "--logical",
        "logical_path",
        required=True,
        help="Ruta lógica (ej. 'bitacoras/2025/semana_38')",
    )
    @click.option(
        "--root",
        "root_path",
        required=True,
        type=click.Path(exists=True, file_okay=False),
        help="Ruta física en el servidor.",
    )
    def scan_folder(project_name: str, logical_path: str, root_path: str) -> None:
        """Escanea una carpeta y sincroniza assets a DB."""

        project = Project.query.filter_by(name=project_name.strip()).first()
        if not project:
            click.echo(f"❌ Proyecto '{project_name}' no existe.")
            raise SystemExit(1)

        folder = Folder.query.filter_by(
            project_id=project.id, logical_path=logical_path.strip()
        ).first()
        if not folder:
            folder = Folder(
                project_id=project.id,
                logical_path=logical_path.strip(),
                fs_path=os.path.abspath(root_path),
            )
            db.session.add(folder)
            db.session.commit()
            click.echo(f"🆕 Folder registrado: {folder.logical_path}")
        else:
            folder.fs_path = os.path.abspath(root_path)
            db.session.commit()

        updated = 0
        created = 0
        skipped = 0

        for base, _, files in os.walk(folder.fs_path):
            for filename in files:
                full = os.path.join(base, filename)
                dir_rel, fname = split_root_rel(full, folder.fs_path)
                rel_path = os.path.join(dir_rel, fname) if dir_rel else fname

                size = os.path.getsize(full)
                digest = sha256_of_file(full)
                mime = guess_mime(full)

                asset = Asset.query.filter_by(
                    project_id=project.id,
                    folder_id=folder.id,
                    relative_path=rel_path,
                ).first()
                if not asset:
                    asset = Asset(
                        project_id=project.id,
                        folder_id=folder.id,
                        filename=fname,
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
        click.echo(
            f"✅ Sincronizado: created={created}, updated={updated}, unchanged={skipped}"
        )

    @app.cli.command("dedupe-assets")
    @click.option("--project", "project_name", required=False, help="Limitar a un proyecto")
    def dedupe_assets(project_name: str | None) -> None:
        """Detecta duplicados por SHA256 y reporta/depura si así lo deseas."""

        query = Asset.query
        if project_name:
            project = Project.query.filter_by(name=project_name.strip()).first()
            if not project:
                click.echo(f"❌ Proyecto '{project_name}' no existe.")
                raise SystemExit(1)
            query = query.filter_by(project_id=project.id)

        rows = query.all()
        by_hash: dict[str, list[Asset]] = {}
        for asset in rows:
            by_hash.setdefault(asset.sha256, []).append(asset)

        duplicates = {digest: items for digest, items in by_hash.items() if len(items) > 1}
        if not duplicates:
            click.echo("✅ No hay duplicados por hash.")
            return

        click.echo("⚠️ Duplicados detectados (sha256 -> count):")
        for digest, items in duplicates.items():
            click.echo(f"- {digest[:10]}… -> {len(items)}")
