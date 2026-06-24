from flask import Blueprint

from webapp.api.responses import success
from webapp.api.validation import ChatRequest, EmptyRequest, validate_json, validate_user_id
from webapp.extensions import chat_limit
from webapp.services.chat_football_service import ChatFootballService

chat_football_v1 = Blueprint("chat_football_v1", __name__)
chat_football_service = ChatFootballService()


@chat_football_v1.route("", methods=["POST"])
@chat_limit
def create_chat():
    user_id = validate_user_id()
    request_json = validate_json(ChatRequest)
    response = chat_football_service.chat(user_id, request_json)
    return success(response, status=201)


@chat_football_v1.route("", methods=["GET"])
def get_chat():
    validate_json(EmptyRequest)
    user_id = validate_user_id()
    response = chat_football_service.get_chat(user_id=user_id)
    return success(response)


@chat_football_v1.route("cache", methods=["GET"])
def get_cache():
    validate_json(EmptyRequest)
    user_id = validate_user_id()
    response = chat_football_service.get_cache(user_id=user_id)
    return success(response)


@chat_football_v1.route("cache", methods=["PUT"])
def refresh_cache():
    validate_json(EmptyRequest)
    user_id = validate_user_id()
    response = chat_football_service.refresh_cache(user_id=user_id)
    return success(response)
