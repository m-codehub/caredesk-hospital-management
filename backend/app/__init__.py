from flask import Flask

from .routes import register_routes


def create_app():
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    app.config["SECRET_KEY"] = "dev-secret-key"

    register_routes(app)
    return app
