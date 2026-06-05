from webapp.api.responses import success
from webapp.api.chat_api import chat
from webapp.api.chat_football_api import chat_football
from webapp.api.chat_general_api import chat_general
from webapp.api.chat_weather_api import chat_weather
from webapp.api.lang_api import lang
from webapp.api.ocr_api import ocr
from webapp.routes.error_handlers import init_error_handlers


def init_routes(flask_app):
    flask_app.url_map.strict_slashes = False

    init_error_handlers(flask_app)

    @flask_app.route("/", methods=["GET"])
    def health_check():
        return success({"status": "OK"})

    flask_app.register_blueprint(chat, url_prefix="/ai/chat/")
    flask_app.register_blueprint(chat_football, url_prefix="/ai/chat/football/")
    flask_app.register_blueprint(chat_general, url_prefix="/ai/chat/general/")
    flask_app.register_blueprint(chat_weather, url_prefix="/ai/chat/weather/")
    flask_app.register_blueprint(lang, url_prefix="/ai/lang/")
    flask_app.register_blueprint(ocr, url_prefix="/ai/ocr/")
