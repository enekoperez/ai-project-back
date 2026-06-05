from flask import Blueprint

from webapp.api.responses import success
from webapp.api.validation import OcrRequest, validate_json
from webapp.services.ocr_service import OcrService

ocr = Blueprint("ocr", __name__)
ocr_service = OcrService()


@ocr.route("", methods=["POST"])
def ask():
    request_json = validate_json(OcrRequest)
    response = ocr_service.ask(request_json)
    return success(response, status=201)
