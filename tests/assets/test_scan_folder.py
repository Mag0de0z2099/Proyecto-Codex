import os

from app.models import Folder, Project
from app.models.asset import Asset


def test_scan_folder_creates_assets(tmp_path, app, db_session):
    with app.app_context():
        project = Project(name="Dragado 2025")
        db_session.add(project)
        db_session.commit()
        project_id = project.id

    folder_path = tmp_path / "semana_38"
    folder_path.mkdir()
    file_path = folder_path / "informe.txt"
    file_path.write_text("hola")

    runner = app.test_cli_runner()
    result = runner.invoke(
        args=[
            "scan-folder",
            "--project",
            "Dragado 2025",
            "--logical",
            "bitacoras/2025/semana_38",
            "--root",
            str(folder_path),
        ]
    )
    assert result.exit_code == 0, result.output

    with app.app_context():
        folder = Folder.query.filter_by(
            project_id=project_id, logical_path="bitacoras/2025/semana_38"
        ).first()
        assert folder is not None
        asset = Asset.query.filter_by(folder_id=folder.id, filename="informe.txt").first()
        assert asset is not None
        assert asset.relative_path == "informe.txt"
        assert asset.size_bytes == os.path.getsize(file_path)
