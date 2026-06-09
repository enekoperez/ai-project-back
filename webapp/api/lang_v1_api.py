from flask import Blueprint

from webapp.api.responses import success
from webapp.api.validation import LangSimpleRequest, validate_json
from webapp.services.lang_service import LangService

lang_v1 = Blueprint("lang_v1", __name__)
lang_service = LangService()


@lang_v1.route("simple", methods=["POST"])
def call_simple():
    request_json = validate_json(LangSimpleRequest)
    response = lang_service.call_simple(request_json)
    return success(response)


@lang_v1.route("complex", methods=["POST"])
def call_complex():
    response = lang_service.call_complex()
    return success(response)
