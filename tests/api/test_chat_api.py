from unittest.mock import Mock

from flask import Flask

from webapp.api.chat_api import chat


def make_client(monkeypatch, service):
    monkeypatch.setattr("webapp.api.chat_api.chat_service", service)

    app = Flask(__name__)
    app.register_blueprint(chat, url_prefix="/ai/chat/")
    return app.test_client()


def test_answer_chat_question_returns_response(monkeypatch):
    service = Mock()
    service.chat.return_value = {
        "id": "chat-1",
        "response": "Use the invoice OCR endpoint.",
        "created_at": "2026-06-01T12:00:00",
    }
    client = make_client(monkeypatch, service)

    request_json = {"user_id": "user-1", "question": "How do I extract invoice totals?"}
    response = client.post("/ai/chat/", json=request_json)

    assert response.status_code == 200
    assert response.get_json() == {
        "id": "chat-1",
        "response": "Use the invoice OCR endpoint.",
        "created_at": "2026-06-01T12:00:00",
    }
    service.chat.assert_called_once_with("user-1", request_json)


def test_answer_chat_question_uses_user_id_header(monkeypatch):
    service = Mock()
    service.chat.return_value = {"chat_log_id": "chat-1"}
    client = make_client(monkeypatch, service)

    request_json = {"user_id": "body-user", "question": "How do I extract invoice totals?"}
    response = client.post("/ai/chat/", json=request_json, headers={"User-Id": "header-user"})

    assert response.status_code == 200
    assert response.get_json() == {"chat_log_id": "chat-1"}
    service.chat.assert_called_once_with("header-user", request_json)


def test_weather_chat_question_returns_response(monkeypatch):
    service = Mock()
    service.weather.return_value = {"chat_log_id": "chat-1", "chat_api_response": "Bad weather in Bilbao."}
    client = make_client(monkeypatch, service)

    request_json = {"user_id": "user-1", "question": "What's the weather in Bilbao?"}
    response = client.post("/ai/chat/weather", json=request_json)

    assert response.status_code == 200
    assert response.get_json() == {"chat_log_id": "chat-1", "chat_api_response": "Bad weather in Bilbao."}
    service.weather.assert_called_once_with("user-1", request_json)


def test_weather_chat_uses_user_id_header(monkeypatch):
    service = Mock()
    service.weather.return_value = {"chat_log_id": "chat-1"}
    client = make_client(monkeypatch, service)

    request_json = {"user_id": "body-user", "question": "What's the weather in Oviedo?"}
    response = client.post("/ai/chat/weather", json=request_json, headers={"User-Id": "header-user"})

    assert response.status_code == 200
    assert response.get_json() == {"chat_log_id": "chat-1"}
    service.weather.assert_called_once_with("header-user", request_json)


def test_get_chat_returns_history_from_body_user_id(monkeypatch):
    service = Mock()
    service.get_chat.return_value = [{"chat_log_id": "chat-1", "role": "user", "text": "Question"}]
    client = make_client(monkeypatch, service)

    response = client.get("/ai/chat/", json={"user_id": "user-1"})

    assert response.status_code == 200
    assert response.get_json() == [{"chat_log_id": "chat-1", "role": "user", "text": "Question"}]
    service.get_chat.assert_called_once_with(user_id="user-1")


def test_get_chat_uses_user_id_header(monkeypatch):
    service = Mock()
    service.get_chat.return_value = []
    client = make_client(monkeypatch, service)

    response = client.get("/ai/chat/", json={"user_id": "body-user"}, headers={"User-Id": "header-user"})

    assert response.status_code == 200
    assert response.get_json() == []
    service.get_chat.assert_called_once_with(user_id="header-user")


def test_like_chat_log_returns_feedback_state(monkeypatch):
    service = Mock()
    service.like.return_value = {"chat_log_id": "chat-1", "liked": True, "disliked": None}
    client = make_client(monkeypatch, service)

    response = client.post("/ai/chat/chat-1/like")

    assert response.status_code == 200
    assert response.get_json() == {
        "chat_log_id": "chat-1",
        "liked": True,
        "disliked": None,
    }
    service.like.assert_called_once_with(chat_log_id="chat-1")


def test_dislike_chat_log_returns_feedback_state(monkeypatch):
    service = Mock()
    service.dislike.return_value = {"chat_log_id": "chat-1", "liked": None, "disliked": True}
    client = make_client(monkeypatch, service)

    response = client.post("/ai/chat/chat-1/dislike")

    assert response.status_code == 200
    assert response.get_json() == {
        "chat_log_id": "chat-1",
        "liked": None,
        "disliked": True,
    }
    service.dislike.assert_called_once_with(chat_log_id="chat-1")


def test_get_chat_like_is_not_available(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get("/ai/chat/chat-1/like")

    assert response.status_code == 405
    service.like.assert_not_called()


def test_get_weather_chat_is_not_available(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get("/ai/chat/weather", json={"user_id": "user-1"})

    assert response.status_code == 405
    service.weather.assert_not_called()
