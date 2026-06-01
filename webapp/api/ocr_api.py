from flask import Blueprint, jsonify

from webapp.services.ocr_service import OcrService

ocr_api = Blueprint("ocr_api", __name__)

ocr_service = OcrService()


@ocr_api.route("", methods=["POST"])
def create_ocr():
    response = ocr_service.create()
    return jsonify(response), 201


@ocr_api.route("", methods=["GET"])
def get_ocrs():
    response = ocr_service.get_all()
    return jsonify(response), 200
