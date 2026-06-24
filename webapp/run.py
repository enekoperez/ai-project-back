from flask import Flask
from mongoengine import connect

from webapp.cli import init_cli
from webapp.config import Config
from webapp.extensions import limiter
from webapp.routes.routes import init_routes


def get_flask_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    connect(host=flask_app.config["DB_CONNECTION_STRING"])
    limiter.init_app(flask_app)
    init_cli(flask_app)
    init_routes(flask_app)
    return flask_app


app = get_flask_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
