from flask import Blueprint

bp_folders = Blueprint("folders", __name__, template_folder="templates")

from . import routes  # noqa: E402,F401
