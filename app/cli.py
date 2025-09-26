import click
from . import db
from .models import User


def register_cli(app):
    @app.cli.command("seed-admin")
    @click.option("--email", required=True)
    @click.option("--password", required=True)
    def seed_admin(email, password):
        """Crea o actualiza el usuario admin."""
        with app.app_context():
            u = User.query.filter_by(email=email).first()
            if not u:
                u = User(email=email, role="admin")
                db.session.add(u)
            u.set_password(password)
            u.role = "admin"
            db.session.commit()
            click.echo(f"Admin listo: {email}")
