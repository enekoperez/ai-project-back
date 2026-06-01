from flask import Blueprint, jsonify

from webapp.services.ocr import OcrService

ocr = Blueprint("ocr", __name__)
ocr_service = OcrService()


@ocr.route("", methods=["POST"])
def create_ocr():
    response = ocr_service.create()
    return jsonify(response), 201


@ocr.route("", methods=["GET"])
def get_ocrs():
    response = ocr_service.get_all()
    return jsonify(response), 200
