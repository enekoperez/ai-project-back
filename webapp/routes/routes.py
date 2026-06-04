from flask import jsonify

from webapp.api.chat_api import chat
from webapp.api.lang_api import lang
from webapp.api.ocr_api import ocr
from webapp.routes.error_handlers import init_error_handlers


def init_routes(flask_app):
    flask_app.url_map.strict_slashes = False

    init_error_handlers(flask_app)

    @flask_app.route("/", methods=["GET"])
    def health_check():
        return jsonify({"status": "OK"}), 200

    flask_app.register_blueprint(chat, url_prefix="/ai/chat/")
    flask_app.register_blueprint(lang, url_prefix="/ai/lang/")
    flask_app.register_blueprint(ocr, url_prefix="/ai/ocr/")
