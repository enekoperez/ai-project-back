from flask import jsonify

from webapp.api.chat import chat
from webapp.api.ocr import ocr


def init_routes(flask_app):
    flask_app.url_map.strict_slashes = False

    @flask_app.route("/", methods=["GET"])
    def health_check():
        return jsonify({"status": "OK"}), 200

    flask_app.register_blueprint(chat, url_prefix="/ai/chat/")
    flask_app.register_blueprint(ocr, url_prefix="/ai/ocr/")
