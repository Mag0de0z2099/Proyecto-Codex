import click
from flask_migrate import upgrade

from app.services.auth_service import ensure_admin_user
from wsgi import app  # importa tu app ya inicializada con Migrate


@click.group()
def cli():
    pass


@cli.command("db-upgrade")
def db_upgrade():
    """Aplica las migraciones de Alembic."""
    with app.app_context():
        upgrade()
        click.echo("DB upgraded successfully")


@cli.command("seed-admin")
@click.option("--email", required=True, help="Correo del administrador")
@click.option(
    "--password",
    required=True,
    help="Contraseña para el administrador",
)
@click.option(
    "--username",
    required=False,
    help="Username opcional (si no se indica se deriva del email)",
)
def seed_admin(email: str, password: str, username: str | None = None):
    """Crea o actualiza el usuario administrador con las credenciales dadas."""

    with app.app_context():
        user = ensure_admin_user(email=email, password=password, username=username)
        click.echo(f"Seeded admin: {user.email} ({user.username})")


if __name__ == "__main__":
    cli()
