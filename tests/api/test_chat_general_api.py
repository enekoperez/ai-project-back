from unittest.mock import Mock

from flask import Flask

from webapp.api.chat_general_v1_api import chat_general_v1
from webapp.routes.error_handlers import init_error_handlers
from response_assertions import assert_error_code, assert_success_response


def make_client(monkeypatch, service):
    monkeypatch.setattr("webapp.api.chat_general_v1_api.chat_general_service", service)

    app = Flask(__name__)
    init_error_handlers(app)
    app.register_blueprint(chat_general_v1, url_prefix="/api/ai/v1/chat/general/")
    return app.test_client()


def test_create_chat_answer_chat_question_returns_response(monkeypatch):
    service = Mock()
    service.chat.return_value = {
        "id": "chat-1",
        "response": "Use the invoice OCR endpoint.",
        "created_at": "2026-06-01T12:00:00",
    }
    client = make_client(monkeypatch, service)

    request_json = {"question": "How do I extract invoice totals?"}
    response = client.post("/api/ai/v1/chat/general/", json=request_json, headers={"User-Id": "user-1"})

    assert response.status_code == 201
    assert_success_response(response, {
        "id": "chat-1",
        "response": "Use the invoice OCR endpoint.",
        "created_at": "2026-06-01T12:00:00",
    })
    service.chat.assert_called_once_with("user-1", request_json)


def test_answer_chat_question_rejects_user_id_in_body(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    request_json = {"user_id": "body-user", "question": "How do I extract invoice totals?"}
    response = client.post("/api/ai/v1/chat/general/", json=request_json, headers={"User-Id": "header-user"})

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.chat.assert_not_called()


def test_answer_chat_question_returns_422_without_question(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.post("/api/ai/v1/chat/general/", json={}, headers={"User-Id": "user-1"})

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.chat.assert_not_called()


def test_answer_chat_question_returns_422_without_user_id(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.post("/api/ai/v1/chat/general/", json={"question": "How do I extract invoice totals?"})

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.chat.assert_not_called()


def test_get_chat_returns_history_from_user_id_header(monkeypatch):
    service = Mock()
    service.get_chat.return_value = [{"chat_log_id": "chat-1", "role": "user", "text": "Question"}]
    client = make_client(monkeypatch, service)

    response = client.get("/api/ai/v1/chat/general/", headers={"User-Id": "user-1"})

    assert response.status_code == 200
    assert_success_response(response, [{"chat_log_id": "chat-1", "role": "user", "text": "Question"}])
    service.get_chat.assert_called_once_with(user_id="user-1")


def test_get_chat_rejects_user_id_in_body(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get("/api/ai/v1/chat/general/", json={"user_id": "body-user"}, headers={"User-Id": "header-user"})

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.get_chat.assert_not_called()


def test_get_chat_returns_422_without_user_id(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get("/api/ai/v1/chat/general/")

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.get_chat.assert_not_called()
