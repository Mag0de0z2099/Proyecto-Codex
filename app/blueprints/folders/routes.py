from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for

from app.db import db
from app.models.folder import Folder
from app.storage import ensure_folder_dir, remove_folder_dir_if_empty
from app.utils.slugify import slugify
from app.authz import login_required

from . import bp_folders


def _get_root() -> Folder:
    root = Folder.query.filter_by(is_root=True).first()
    if not root:
        root = Folder(name="Raíz", slug="raiz", is_root=True, parent_id=None)
        db.session.add(root)
        db.session.commit()
        ensure_folder_dir(root.id)
    return root


@bp_folders.get("/")
@login_required
def index():
    root = _get_root()
    top = Folder.query.filter_by(parent_id=root.id).order_by(Folder.name.asc()).all()
    return render_template("folders/index.html", root=root, top=top)


@bp_folders.get("/<int:folder_id>")
@login_required
def show(folder_id: int):
    folder = db.session.get(Folder, folder_id) or _get_root()
    children = Folder.query.filter_by(parent_id=folder.id).order_by(Folder.name.asc()).all()
    parent = db.session.get(Folder, folder.parent_id) if folder.parent_id else None
    trail: list[Folder] = []
    current = folder
    while current:
        trail.append(current)
        current = current.parent if current.parent_id else None
    trail.reverse()
    return render_template(
        "folders/show.html",
        folder=folder,
        parent=parent,
        children=children,
        trail=trail,
    )


@bp_folders.post("/create")
@login_required
def create():
    parent_id = request.form.get("parent_id", type=int)
    name = (request.form.get("name") or "").strip()
    if not name:
        flash("Nombre requerido.", "warning")
        return redirect(request.referrer or url_for("folders.index"))

    parent = db.session.get(Folder, parent_id) if parent_id else _get_root()
    slug = slugify(name)
    exists = Folder.query.filter_by(parent_id=parent.id, slug=slug).first()
    if exists:
        flash("Ya existe una carpeta con ese nombre en el mismo nivel.", "danger")
        return redirect(url_for("folders.show", folder_id=parent.id))

    folder = Folder(name=name, slug=slug, parent_id=parent.id)
    db.session.add(folder)
    db.session.commit()
    ensure_folder_dir(folder.id)
    flash("Carpeta creada.", "success")
    return redirect(url_for("folders.show", folder_id=parent.id))


@bp_folders.post("/rename/<int:folder_id>")
@login_required
def rename(folder_id: int):
    folder = db.session.get(Folder, folder_id)
    if not folder or folder.is_root:
        flash("No se puede renombrar la raíz o carpeta inexistente.", "warning")
        return redirect(request.referrer or url_for("folders.index"))

    new_name = (request.form.get("name") or "").strip()
    if not new_name:
        flash("Nombre requerido.", "warning")
        return redirect(url_for("folders.show", folder_id=folder.parent_id or folder.id))

    new_slug = slugify(new_name)
    duplicate = (
        Folder.query.filter(
            Folder.parent_id == folder.parent_id,
            Folder.slug == new_slug,
            Folder.id != folder.id,
        )
        .first()
    )
    if duplicate:
        flash("Ya existe una carpeta con ese nombre en ese nivel.", "danger")
        return redirect(url_for("folders.show", folder_id=folder.parent_id or folder.id))

    folder.name = new_name
    folder.slug = new_slug
    db.session.commit()
    flash("Carpeta renombrada.", "success")
    return redirect(url_for("folders.show", folder_id=folder.parent_id or folder.id))


@bp_folders.post("/move/<int:folder_id>")
@login_required
def move(folder_id: int):
    folder = db.session.get(Folder, folder_id)
    if not folder or folder.is_root:
        flash("No se puede mover la raíz o carpeta inexistente.", "warning")
        return redirect(request.referrer or url_for("folders.index"))

    new_parent_id = request.form.get("parent_id", type=int)
    new_parent = db.session.get(Folder, new_parent_id) if new_parent_id else _get_root()
    if new_parent.id == folder.id:
        flash("No puedes mover una carpeta dentro de sí misma.", "danger")
        return redirect(url_for("folders.show", folder_id=folder.parent_id or folder.id))

    current = new_parent
    while current:
        if current.id == folder.id:
            flash("Movimiento inválido (crearía un ciclo).", "danger")
            return redirect(url_for("folders.show", folder_id=folder.parent_id or folder.id))
        current = db.session.get(Folder, current.parent_id) if current.parent_id else None

    duplicate = (
        Folder.query.filter(
            Folder.parent_id == new_parent.id,
            Folder.slug == folder.slug,
            Folder.id != folder.id,
        )
        .first()
    )
    if duplicate:
        flash("Ya existe una carpeta con ese nombre en el destino.", "danger")
        return redirect(url_for("folders.show", folder_id=folder.parent_id or folder.id))

    folder.parent_id = new_parent.id
    db.session.commit()
    flash("Carpeta movida.", "success")
    return redirect(url_for("folders.show", folder_id=new_parent.id))


@bp_folders.post("/delete/<int:folder_id>")
@login_required
def delete(folder_id: int):
    folder = db.session.get(Folder, folder_id)
    if not folder or folder.is_root:
        flash("No se puede eliminar la raíz o carpeta inexistente.", "warning")
        return redirect(request.referrer or url_for("folders.index"))

    if folder.children:
        flash("La carpeta tiene subcarpetas. Elimina o mueve primero su contenido.", "warning")
        return redirect(url_for("folders.show", folder_id=folder.id))

    parent_id = folder.parent_id
    db.session.delete(folder)
    db.session.commit()

    remove_folder_dir_if_empty(folder_id)

    flash("Carpeta eliminada.", "success")
    return redirect(url_for("folders.show", folder_id=parent_id or _get_root().id))
