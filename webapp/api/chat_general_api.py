from flask import Blueprint, jsonify

from webapp.api.validation import ChatRequest, validate_json, validate_user_id
from webapp.services.chat_general_service import ChatGeneralService

chat_general = Blueprint("chat_general", __name__)
chat_general_service = ChatGeneralService()


@chat_general.route("", methods=["POST"])
def create_chat():
    user_id = validate_user_id()
    request_json = validate_json(ChatRequest)
    response = chat_general_service.chat(user_id, request_json)
    return jsonify(response), 200


@chat_general.route("", methods=["GET"])
def get_chat():
    user_id = validate_user_id()
    response = chat_general_service.get_chat(user_id=user_id)
    return jsonify(response), 200
