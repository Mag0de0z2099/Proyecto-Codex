# app/auth0.py
import os
from functools import wraps
from flask import Blueprint, redirect, session, request, abort
from authlib.integrations.flask_client import OAuth

bp = Blueprint("auth", __name__)
oauth = OAuth()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_CALLBACK_URL = os.getenv("AUTH0_CALLBACK_URL")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")  # opcional

def init_auth0(app):
    oauth.init_app(app)
    app.auth0 = oauth.register(
        "auth0",
        client_id=AUTH0_CLIENT_ID,
        client_secret=AUTH0_CLIENT_SECRET,
        client_kwargs={"scope": "openid profile email"},
        server_metadata_url=f"https://{AUTH0_DOMAIN}/.well-known/openid-configuration",
    )
    app.register_blueprint(bp)

@bp.get("/login")
def login():
    # Si definiste audience (API RS256 en Auth0), inclúyelo
    params = {}
    if AUTH0_AUDIENCE:
        params["audience"] = AUTH0_AUDIENCE
    return redirect(bp._get_current_object().app.auth0.authorize_redirect(
        redirect_uri=AUTH0_CALLBACK_URL,
        **params
    ))

@bp.get("/callback")
def callback():
    token = bp._get_current_object().app.auth0.authorize_access_token()
    # userinfo OIDC estándar
    session["user"] = token.get("userinfo")
    # access token (si pediste audience para llamar APIs)
    session["access_token"] = token.get("access_token")
    return redirect("/")

@bp.get("/logout")
def logout():
    session.clear()
    return redirect("/")

# --- utilidades ---

def requires_login(view):
    """Decorador sencillo basado en sesión de OIDC (userinfo)."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect("/login")
        return view(*args, **kwargs)
    return wrapper
