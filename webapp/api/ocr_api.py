from flask import Blueprint, jsonify, request

from webapp.services.ocr_service import OcrService

ocr = Blueprint("ocr", __name__)
ocr_service = OcrService()


@ocr.route("", methods=["POST"])
def ask():
    response = ocr_service.ask(request.json)
    return jsonify(response), 200
