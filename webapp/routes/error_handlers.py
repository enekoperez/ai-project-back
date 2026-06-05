from flask import jsonify
from werkzeug.exceptions import HTTPException

from webapp.api.validation import RequestValidationError


def init_error_handlers(flask_app):
    @flask_app.errorhandler(RequestValidationError)
    def handle_validation_error(error):
        return jsonify({
            "error": {
                "code": "validation_error",
                "message": error.description,
                "details": error.errors,
            }
        }), 422

    @flask_app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({
            "error": {
                "code": error.name.lower().replace(" ", "_"),
                "message": error.description,
            }
        }), error.code

    @flask_app.errorhandler(Exception)
    def handle_unexpected_error(error):
        return jsonify({
            "error": {
                "code": "internal_server_error",
                "message": "Internal server error",
            }
        }), 500
