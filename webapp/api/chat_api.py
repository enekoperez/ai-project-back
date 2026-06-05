from flask import Blueprint, jsonify

from webapp.api.validation import ChatLogPathRequest, ChatRequest, validate_data, validate_json, validate_user_id
from webapp.services.chat_football_service import ChatFootballService
from webapp.services.chat_service import ChatService
from webapp.services.chat_weather_service import ChatWeatherService

chat = Blueprint("chat", __name__)
chat_football_service = ChatFootballService()
chat_service = ChatService()
chat_weather_service = ChatWeatherService()


@chat.route("", methods=["POST"])
def create_chat():
    user_id = validate_user_id()
    request_json = validate_json(ChatRequest)
    response = chat_service.chat(user_id, request_json)
    return jsonify(response), 200


@chat.route("", methods=["GET"])
def get_chat():
    user_id = validate_user_id()
    response = chat_service.get_chat(user_id=user_id)
    return jsonify(response), 200


@chat.route("weather", methods=["POST"])
def create_chat_weather():
    user_id = validate_user_id()
    request_json = validate_json(ChatRequest)
    response = chat_weather_service.chat(user_id, request_json)
    return jsonify(response), 200


@chat.route("football", methods=["POST"])
def create_chat_football():
    user_id = validate_user_id()
    request_json = validate_json(ChatRequest)
    response = chat_football_service.chat(user_id, request_json)
    return jsonify(response), 200


@chat.route("<chat_log_id>/like", methods=["POST"])
def like(chat_log_id):
    validate_data(ChatLogPathRequest, {"chat_log_id": chat_log_id})
    response = chat_service.like(chat_log_id=chat_log_id)
    return jsonify(response), 200


@chat.route("<chat_log_id>/dislike", methods=["POST"])
def dislike(chat_log_id):
    validate_data(ChatLogPathRequest, {"chat_log_id": chat_log_id})
    response = chat_service.dislike(chat_log_id=chat_log_id)
    return jsonify(response), 200
