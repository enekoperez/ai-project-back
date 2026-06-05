from flask import Blueprint, jsonify

from webapp.api.validation import ChatLogPathRequest, validate_data
from webapp.services.chat_service import ChatService

chat = Blueprint("chat", __name__)
chat_service = ChatService()


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
