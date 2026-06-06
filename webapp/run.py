from flask import Flask
from mongoengine import connect

from webapp.cli import init_cli
from webapp.config import Config
from webapp.routes.routes import init_routes


def get_flask_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    connect(host=flask_app.config["DB_CONNECTION_STRING"])
    init_cli(flask_app)
    init_routes(flask_app)
    return flask_app


app = get_flask_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
