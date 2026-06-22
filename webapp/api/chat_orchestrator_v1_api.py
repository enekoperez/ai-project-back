from flask import Blueprint

from webapp.api.validation import ChatRequest, validate_json
from webapp.services.chat_orchestrator_service import ChatOrchestratorService

chat_orchestrator_v1 = Blueprint("chat_orchestrator_v1", __name__)
chat_orchestrator_service = ChatOrchestratorService()


@chat_orchestrator_v1.route("", methods=["POST"])
def create_chat():
    request_json = validate_json(ChatRequest)
    html = chat_orchestrator_service.chat(request_json)
    return html, 201, {"Content-Type": "text/html; charset=utf-8"}
