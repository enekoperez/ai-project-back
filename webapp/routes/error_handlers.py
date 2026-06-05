from werkzeug.exceptions import HTTPException

from webapp.api.responses import failure
from webapp.api.validation import RequestValidationError


def init_error_handlers(flask_app):
    @flask_app.errorhandler(RequestValidationError)
    def handle_validation_error(error):
        return failure(
            code="validation_error",
            message=error.description,
            details=error.errors,
            status=422,
        )

    @flask_app.errorhandler(HTTPException)
    def handle_http_error(error):
        return failure(
            code=error.name.lower().replace(" ", "_"),
            message=error.description,
            status=error.code,
        )

    @flask_app.errorhandler(Exception)
    def handle_unexpected_error(error):
        return failure(
            code="internal_server_error",
            message="Internal server error",
            status=500,
        )
