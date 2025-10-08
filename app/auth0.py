import os
from typing import Optional

from flask import Blueprint, current_app, redirect, session
from authlib.integrations.flask_client import OAuth

bp = Blueprint("auth0", __name__)
oauth = OAuth()


def _is_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() not in {"0", "false", "no", "off"}


def is_auth0_enabled() -> bool:
    required_envs = [
        "AUTH0_DOMAIN",
        "AUTH0_CLIENT_ID",
        "AUTH0_CLIENT_SECRET",
        "AUTH0_CALLBACK_URL",
    ]
    if not _is_truthy(os.getenv("ENABLE_AUTH0", "false")):
        return False
    return all(os.getenv(name) for name in required_envs)


def init_auth0(app) -> None:
    if not is_auth0_enabled():
        if bp.name not in app.blueprints:
            app.register_blueprint(bp)
        return

    oauth.init_app(app)
    app.auth0 = oauth.register(
        "auth0",
        client_id=os.getenv("AUTH0_CLIENT_ID"),
        client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
        client_kwargs={"scope": "openid profile email"},
        server_metadata_url=f"https://{os.getenv('AUTH0_DOMAIN')}/.well-known/openid-configuration",
    )
    if bp.name not in app.blueprints:
        app.register_blueprint(bp)


@bp.get("/login")
def login():
    if not is_auth0_enabled():
        return {"auth": "disabled"}, 200

    auth0_client = getattr(current_app, "auth0", None)
    if auth0_client is None:
        return {"error": "auth_not_configured"}, 503

    return redirect(
        auth0_client.authorize_redirect(
            redirect_uri=os.getenv("AUTH0_CALLBACK_URL")
        )
    )


@bp.get("/callback")
def callback():
    if not is_auth0_enabled():
        session.clear()
        return {"auth": "disabled"}, 200

    auth0_client = getattr(current_app, "auth0", None)
    if auth0_client is None:
        return {"error": "auth_not_configured"}, 503

    token = auth0_client.authorize_access_token()
    session["user"] = token.get("userinfo")
    session["access_token"] = token.get("access_token")
    return redirect("/")


@bp.get("/logout")
def logout():
    session.clear()
    if not is_auth0_enabled():
        return {"ok": True}, 200
    return redirect("/")
