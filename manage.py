from datetime import datetime, timezone

import click
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User
from app.services.maintenance_service import cleanup_expired_refresh_tokens

app = create_app()


@app.cli.command("seed-admin")
@click.option("--email", required=True)
@click.option("--password", required=True)
def seed_admin(email: str, password: str) -> None:
    with app.app_context():
        user = User.query.filter_by(email=email).one_or_none()
        if user is None:
            username = email.split("@", 1)[0]
            user = User(email=email, username=username)
            db.session.add(user)

        if hasattr(user, "set_password"):
            user.set_password(password)
        else:
            user.password_hash = generate_password_hash(password)

        if hasattr(user, "role"):
            user.role = "admin"
        if hasattr(user, "is_admin"):
            user.is_admin = True
        if hasattr(user, "is_active"):
            user.is_active = True
        if hasattr(user, "status"):
            user.status = "approved"
        if hasattr(user, "is_approved"):
            user.is_approved = True
        if hasattr(user, "approved_at"):
            user.approved_at = datetime.now(timezone.utc)
        if hasattr(user, "force_change_password"):
            user.force_change_password = False

        db.session.commit()
        click.echo(f"Seeded admin: {email}")


@app.cli.command("cleanup-refresh")
@click.option("--grace-days", default=0, show_default=True, help="Días de gracia para conservar expirados.")
def cleanup_refresh(grace_days: int) -> None:
    """Delete expired refresh tokens using optional grace days."""

    with app.app_context():
        result = cleanup_expired_refresh_tokens(grace_days=grace_days)
        click.echo(f"Cleanup done: {result}")


if __name__ == "__main__":
    app.cli.main()
