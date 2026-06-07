from unittest.mock import Mock

from flask import Flask

from webapp.api.chat_weather_api import chat_weather
from webapp.routes.error_handlers import init_error_handlers
from response_assertions import assert_error_code, assert_success_response


def make_client(monkeypatch, service):
    monkeypatch.setattr("webapp.api.chat_weather_api.chat_weather_service", service)

    app = Flask(__name__)
    init_error_handlers(app)
    app.register_blueprint(chat_weather, url_prefix="/ai/chat/weather/")
    return app.test_client()


def test_create_chat_weather_question_returns_response(monkeypatch):
    service = Mock()
    service.chat.return_value = {"chat_log_id": "chat-1", "chat_api_response": "Bad weather in Bilbao."}
    client = make_client(monkeypatch, service)

    request_json = {"question": "What's the weather in Bilbao?"}
    response = client.post("/ai/chat/weather/", json=request_json, headers={"User-Id": "user-1"})

    assert response.status_code == 201
    assert_success_response(response, {"chat_log_id": "chat-1", "chat_api_response": "Bad weather in Bilbao."})
    service.chat.assert_called_once_with("user-1", request_json)


def test_chat_weather_rejects_user_id_in_body(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    request_json = {"user_id": "body-user", "question": "What's the weather in Oviedo?"}
    response = client.post("/ai/chat/weather/", json=request_json, headers={"User-Id": "header-user"})

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.chat.assert_not_called()


def test_chat_weather_returns_422_for_empty_question(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.post("/ai/chat/weather/", json={"question": " "}, headers={"User-Id": "user-1"})

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.chat.assert_not_called()


def test_get_chat_weather_returns_history_from_user_id_header(monkeypatch):
    service = Mock()
    service.get_chat.return_value = [{"chat_log_id": "chat-1", "role": "user", "text": "Weather?"}]
    client = make_client(monkeypatch, service)

    response = client.get("/ai/chat/weather/", headers={"User-Id": "user-1"})

    assert response.status_code == 200
    assert_success_response(response, [{"chat_log_id": "chat-1", "role": "user", "text": "Weather?"}])
    service.get_chat.assert_called_once_with(user_id="user-1")


def test_get_chat_weather_rejects_user_id_in_body(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get("/ai/chat/weather/", json={"user_id": "body-user"}, headers={"User-Id": "header-user"})

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.get_chat.assert_not_called()


def test_get_chat_weather_returns_422_without_user_id(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get("/ai/chat/weather/")

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.get_chat.assert_not_called()
