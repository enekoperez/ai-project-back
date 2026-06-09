from flask import Blueprint

from webapp.api.responses import success
from webapp.api.validation import OcrRequest, validate_json
from webapp.services.ocr_service import OcrService

ocr_v1 = Blueprint("ocr_v1", __name__)
ocr_service = OcrService()


@ocr_v1.route("", methods=["POST"])
def ask():
    request_json = validate_json(OcrRequest)
    response = ocr_service.ask(request_json)
    return success(response, status=201)
