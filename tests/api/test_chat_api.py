from unittest.mock import Mock

from flask import Flask

from webapp.api.chat_v1_api import chat_v1
from webapp.routes.error_handlers import init_error_handlers
from response_assertions import assert_error_code, assert_success_response


def make_client(monkeypatch, service):
    monkeypatch.setattr("webapp.api.chat_v1_api.chat_service", service)

    app = Flask(__name__)
    init_error_handlers(app)
    app.register_blueprint(chat_v1, url_prefix="/ai/v1/chat/")
    return app.test_client()


def test_like_chat_log_returns_feedback_state(monkeypatch):
    service = Mock()
    service.like.return_value = {"chat_log_id": "chat-1", "liked": True, "disliked": None}
    client = make_client(monkeypatch, service)

    response = client.put("/ai/v1/chat/chat-1/like")

    assert response.status_code == 200
    assert_success_response(response, {
        "chat_log_id": "chat-1",
        "liked": True,
        "disliked": None,
    })
    service.like.assert_called_once_with(chat_log_id="chat-1")


def test_like_chat_log_returns_422_for_blank_path_id(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.put("/ai/v1/chat/%20/like")

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.like.assert_not_called()


def test_dislike_chat_log_returns_feedback_state(monkeypatch):
    service = Mock()
    service.dislike.return_value = {"chat_log_id": "chat-1", "liked": None, "disliked": True}
    client = make_client(monkeypatch, service)

    response = client.put("/ai/v1/chat/chat-1/dislike")

    assert response.status_code == 200
    assert_success_response(response, {
        "chat_log_id": "chat-1",
        "liked": None,
        "disliked": True,
    })
    service.dislike.assert_called_once_with(chat_log_id="chat-1")
