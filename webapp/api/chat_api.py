from flask import Blueprint, jsonify, request

from webapp.services.chat_service import ChatService

chat = Blueprint("chat", __name__)
chat_service = ChatService()


@chat.route("", methods=["POST"])
def ask():
    response = chat_service.ask(request.json)
    return jsonify(response), 200
