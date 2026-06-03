from flask import Blueprint, jsonify, request

from webapp.services.lang_service import LangService

lang = Blueprint("lang", __name__)
lang_service = LangService()


@lang.route("simple", methods=["POST"])
def call_simple():
    response = lang_service.call_simple(request.json)
    return jsonify(response), 200


@lang.route("complex", methods=["POST"])
def call_complex():
    response = lang_service.call_complex()
    return jsonify(response), 200
