# manage.py
import click
from alembic import command
from alembic.config import Config
from flask.cli import with_appcontext

from app import create_app

app = create_app()


def _alembic_cfg() -> Config:
    cfg = Config("migrations/alembic.ini")
    # Alembic tomará la URL desde env.py (inyectada por la app)
    return cfg


@app.cli.command("db-upgrade")
@with_appcontext
def db_upgrade():
    """Aplica las migraciones hasta head."""
    command.upgrade(_alembic_cfg(), "head")
    click.echo("✅ Alembic upgrade head OK")


@app.cli.command("db-downgrade")
@click.argument("rev", default="-1")
@with_appcontext
def db_downgrade(rev):
    """Revierte una migración. Por defecto: -1 (una atrás)."""
    command.downgrade(_alembic_cfg(), rev)
    click.echo(f"✅ Alembic downgrade {rev} OK")


@app.cli.command("seed-admin")
@click.option("--email", required=True)
@click.option("--password", required=True)
@with_appcontext
def seed_admin(email, password):
    """
    Crea/asegura usuario admin. Si ya tienes un 'flask seed-admin' nativo en app/cli.py,
    puedes borrar este o mantenerlo; no hay conflicto si el endpoint tiene otro nombre.
    """
    try:
        from app.models import User  # ajusta el import a tu estructura real
        from app import db

        email_n = email.strip().lower()
        user = User.query.filter_by(email=email_n).first()
        if user:
            click.echo("ℹ️ Admin ya existe; no se cambia la contraseña.")
            return

        user = User(
            email=email_n,
            username="admin",
            is_admin=True,
            is_active=True,
            role="admin",
            title="Administrator",
        )
        user.set_password(password)  # asegúrate que tu modelo tenga este método
        db.session.add(user)
        db.session.commit()
        click.echo("✅ Admin creado.")
    except Exception as e:
        click.echo(f"❌ Error seeding admin: {e}")
        raise


if __name__ == "__main__":
    # Uso directo (equivalente a 'flask run'); en Render usamos gunicorn
    app.run(host="0.0.0.0", port=5000)
