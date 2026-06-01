from flask import Blueprint, jsonify

from webapp.services.chat_service import ChatService

chat_api = Blueprint("chat_api", __name__)

chat_service = ChatService()


@chat_api.route("", methods=["POST"])
def create_chat():
    response = chat_service.create()
    return jsonify(response), 201


@chat_api.route("", methods=["GET"])
def get_chats():
    response = chat_service.get_all()
    return jsonify(response), 200
