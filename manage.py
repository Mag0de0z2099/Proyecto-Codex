import click
from flask_migrate import upgrade
from app.main import app  # importa tu app ya inicializada con Migrate


@click.group()
def cli():
    pass


@cli.command("db-upgrade")
def db_upgrade():
    """Aplica las migraciones de Alembic."""
    with app.app_context():
        upgrade()
        click.echo("DB upgraded successfully")


if __name__ == "__main__":
    cli()
