from __future__ import annotations

from pathlib import Path

from flask import current_app, render_template
from flask_login import login_required

from . import bp_admin


@bp_admin.get("/")
@login_required
def index():
    return render_template("admin/index.html")


@bp_admin.get("/files")
@login_required
def list_files():
    data_dir = Path(current_app.config["DATA_DIR"])
    items: list[dict[str, object]] = []

    for path in sorted(data_dir.glob("**/*")):
        relative = path.relative_to(data_dir).as_posix()
        items.append(
            {
                "name": relative,
                "is_dir": path.is_dir(),
                "size": path.stat().st_size if path.is_file() else None,
            }
        )

    return render_template("admin/files.html", items=items, base=str(data_dir))
