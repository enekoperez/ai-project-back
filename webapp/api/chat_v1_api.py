from flask import Blueprint

from webapp.api.responses import success
from webapp.api.validation import ChatLogPathRequest, EmptyRequest, validate_data, validate_json
from webapp.services.chat_service import ChatService

chat_v1 = Blueprint("chat_v1", __name__)
chat_service = ChatService()


@chat_v1.route("<chat_log_id>/like", methods=["PUT"])
def like(chat_log_id):
    validate_json(EmptyRequest)
    validate_data(ChatLogPathRequest, {"chat_log_id": chat_log_id})
    response = chat_service.like(chat_log_id=chat_log_id)
    return success(response)


@chat_v1.route("<chat_log_id>/dislike", methods=["PUT"])
def dislike(chat_log_id):
    validate_json(EmptyRequest)
    validate_data(ChatLogPathRequest, {"chat_log_id": chat_log_id})
    response = chat_service.dislike(chat_log_id=chat_log_id)
    return success(response)
