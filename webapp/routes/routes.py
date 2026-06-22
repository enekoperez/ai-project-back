from flask import send_from_directory

from webapp.api.chat_football_v1_api import chat_football_v1
from webapp.api.chat_general_v1_api import chat_general_v1
from webapp.api.chat_v1_api import chat_v1
from webapp.api.chat_weather_v1_api import chat_weather_v1
from webapp.api.ocr_v1_api import ocr_v1
from webapp.api.responses import success
from webapp.routes.error_handlers import init_error_handlers

V1_PREFIX = "/ai/v1"


def init_routes(flask_app):
    flask_app.url_map.strict_slashes = False

    init_error_handlers(flask_app)

    @flask_app.route("/", methods=["GET"])
    def health_check():
        return success({"status": "OK"})

    @flask_app.route("/ui", methods=["GET"])
    def ui():
        return send_from_directory(flask_app.static_folder, "index.html")

    flask_app.register_blueprint(chat_v1, url_prefix=f"{V1_PREFIX}/chat/")
    flask_app.register_blueprint(chat_football_v1, url_prefix=f"{V1_PREFIX}/chat/football/")
    flask_app.register_blueprint(chat_general_v1, url_prefix=f"{V1_PREFIX}/chat/general/")
    flask_app.register_blueprint(chat_weather_v1, url_prefix=f"{V1_PREFIX}/chat/weather/")
    flask_app.register_blueprint(ocr_v1, url_prefix=f"{V1_PREFIX}/ocr/")
