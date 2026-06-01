from flask import jsonify

from webapp.api.chat_api import chat_api
from webapp.api.ocr_api import ocr_api


def init_routes(flask_app):
    flask_app.url_map.strict_slashes = False

    @flask_app.route("/", methods=["GET"])
    def health_check():
        return jsonify({"status": "OK"}), 200

    flask_app.register_blueprint(ocr_api, url_prefix="/ai/ocr/")
    flask_app.register_blueprint(chat_api, url_prefix="/ai/chat/")
