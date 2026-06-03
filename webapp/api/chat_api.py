from flask import Blueprint, jsonify, request

from webapp.services.chat_service import ChatService

chat = Blueprint("chat", __name__)
chat_service = ChatService()


def _request_user_id():
    request_json = request.get_json(silent=True) or {}
    return request.headers.get('User-Id') or request_json['user_id']


@chat.route("", methods=["POST"])
def create_chat():
    user_id = _request_user_id()
    response = chat_service.chat(user_id, request.json)
    return jsonify(response), 200


@chat.route("", methods=["GET"])
def get_chat():
    user_id = _request_user_id()
    response = chat_service.get_chat(user_id=user_id)
    return jsonify(response), 200


@chat.route("weather", methods=["POST"])
def create_weather_chat():
    user_id = _request_user_id()
    response = chat_service.weather(user_id, request.json)
    return jsonify(response), 200


@chat.route("<chat_log_id>/like", methods=["POST"])
def like(chat_log_id):
    response = chat_service.like(chat_log_id=chat_log_id)
    return jsonify(response), 200


@chat.route("<chat_log_id>/dislike", methods=["POST"])
def dislike(chat_log_id):
    response = chat_service.dislike(chat_log_id=chat_log_id)
    return jsonify(response), 200
