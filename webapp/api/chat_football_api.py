from flask import Blueprint, jsonify

from webapp.api.validation import ChatRequest, validate_json, validate_user_id
from webapp.services.chat_football_service import ChatFootballService

chat_football = Blueprint("chat_football", __name__)
chat_football_service = ChatFootballService()


@chat_football.route("", methods=["POST"])
def create_chat():
    user_id = validate_user_id()
    request_json = validate_json(ChatRequest)
    response = chat_football_service.chat(user_id, request_json)
    return jsonify(response), 200


@chat_football.route("", methods=["GET"])
def get_chat():
    user_id = validate_user_id()
    response = chat_football_service.get_chat(user_id=user_id)
    return jsonify(response), 200


@chat_football.route("cache", methods=["GET"])
def get_cache():
    user_id = validate_user_id()
    response = chat_football_service.get_cache(user_id=user_id)
    return jsonify(response), 200


@chat_football.route("cache", methods=["PUT"])
def refresh_cache():
    user_id = validate_user_id()
    response = chat_football_service.refresh_cache(user_id=user_id)
    return jsonify(response), 200
