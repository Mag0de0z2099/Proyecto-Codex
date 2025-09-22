# manage.py
import click
from alembic import command
from alembic.config import Config
from flask.cli import with_appcontext

from app import create_app

app = create_app()


def _alembic_cfg() -> Config:
    cfg = Config("migrations/alembic.ini")
    return cfg


@app.cli.command("db-upgrade")
@with_appcontext
def db_upgrade():
    command.upgrade(_alembic_cfg(), "head")
    click.echo("✅ Alembic upgrade head OK")


@app.cli.command("db-downgrade")
@click.argument("rev", default="-1")
@with_appcontext
def db_downgrade(rev):
    command.downgrade(_alembic_cfg(), rev)
    click.echo(f"✅ Alembic downgrade {rev} OK")
