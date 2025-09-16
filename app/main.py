from flask import Flask
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")


@app.route("/")
def home():
    return "Hola desde Elyra + Render 🚀"


@app.route("/health")
def health():
    return "ok", 200
