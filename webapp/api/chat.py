from flask import Blueprint, jsonify

from webapp.services.chat import ChatService

chat = Blueprint("chat", __name__)
chat_service = ChatService()


@chat.route("", methods=["POST"])
def create_chat():
    response = chat_service.create()
    return jsonify(response), 201


@chat.route("", methods=["GET"])
def get_chats():
    response = chat_service.get_all()
    return jsonify(response), 200
