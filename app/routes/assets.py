from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.models.asset import Asset

assets_bp = Blueprint("assets", __name__, url_prefix="/api/assets")


@assets_bp.get("")
def list_assets():
    project_id = request.args.get("project_id", type=int)
    folder_id = request.args.get("folder_id", type=int)

    query = Asset.query
    if project_id is not None:
        query = query.filter_by(project_id=project_id)
    if folder_id is not None:
        query = query.filter_by(folder_id=folder_id)

    items = query.order_by(Asset.created_at.desc()).limit(200).all()
    return jsonify(
        [
            {
                "id": asset.id,
                "project_id": asset.project_id,
                "folder_id": asset.folder_id,
                "filename": asset.filename,
                "relative_path": asset.relative_path,
                "size_bytes": asset.size_bytes,
                "sha256": asset.sha256,
                "mime_type": asset.mime_type,
                "version": asset.version,
            }
            for asset in items
        ]
    )
