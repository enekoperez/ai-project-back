from unittest.mock import Mock

from flask import Flask

from webapp.api.chat_football_v1_api import chat_football_v1
from webapp.routes.error_handlers import init_error_handlers
from response_assertions import assert_error_code, assert_success_response


def make_client(monkeypatch, service):
    monkeypatch.setattr("webapp.api.chat_football_v1_api.chat_football_service", service)

    app = Flask(__name__)
    init_error_handlers(app)
    app.register_blueprint(chat_football_v1, url_prefix="/ai/v1/chat/football/")
    return app.test_client()


def test_create_chat_football_question_returns_response(monkeypatch):
    service = Mock()
    service.chat.return_value = {"chat_log_id": "chat-1", "chat_api_response": "Football teams have eleven players."}
    client = make_client(monkeypatch, service)

    request_json = {"question": "How many players are on a football team?"}
    response = client.post("/ai/v1/chat/football/", json=request_json, headers={"User-Id": "user-1"})

    assert response.status_code == 201
    assert_success_response(response, {"chat_log_id": "chat-1", "chat_api_response": "Football teams have eleven players."})
    service.chat.assert_called_once_with("user-1", request_json)


def test_chat_football_rejects_user_id_in_body(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    request_json = {"user_id": "body-user", "question": "Who won?"}
    response = client.post("/ai/v1/chat/football/", json=request_json, headers={"User-Id": "header-user"})

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.chat.assert_not_called()


def test_chat_football_returns_422_without_json(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.post("/ai/v1/chat/football/")

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.chat.assert_not_called()


def test_get_chat_football_returns_history_from_user_id_header(monkeypatch):
    service = Mock()
    service.get_chat.return_value = [{"chat_log_id": "chat-1", "role": "user", "text": "Who won?"}]
    client = make_client(monkeypatch, service)

    response = client.get("/ai/v1/chat/football/", headers={"User-Id": "user-1"})

    assert response.status_code == 200
    assert_success_response(response, [{"chat_log_id": "chat-1", "role": "user", "text": "Who won?"}])
    service.get_chat.assert_called_once_with(user_id="user-1")


def test_get_chat_football_rejects_user_id_in_body(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get("/ai/v1/chat/football/", json={"user_id": "body-user"}, headers={"User-Id": "header-user"})

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.get_chat.assert_not_called()


def test_get_chat_football_returns_422_without_user_id(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get("/ai/v1/chat/football/")

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.get_chat.assert_not_called()


def test_get_cache_returns_cache_create_time(monkeypatch):
    service = Mock()
    service.get_cache.return_value = {
        "cache_create_time": "2026-06-01T12:00:00+00:00",
        "cache_create_time_utc_in_millis": 1780315200000,
    }
    client = make_client(monkeypatch, service)

    response = client.get("/ai/v1/chat/football/cache", headers={"User-Id": "user-1"})

    assert response.status_code == 200
    assert_success_response(response, {
        "cache_create_time": "2026-06-01T12:00:00+00:00",
        "cache_create_time_utc_in_millis": 1780315200000,
    })
    service.get_cache.assert_called_once_with(user_id="user-1")


def test_get_chat_football_cache_rejects_user_id_in_body(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get(
        "/ai/v1/chat/football/cache",
        json={"user_id": "body-user"},
        headers={"User-Id": "header-user"},
    )

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.get_cache.assert_not_called()


def test_get_chat_football_cache_returns_422_without_user_id(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get("/ai/v1/chat/football/cache")

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.get_cache.assert_not_called()


def test_refresh_cache_returns_cache_create_time(monkeypatch):
    service = Mock()
    service.refresh_cache.return_value = {
        "cache_create_time": "2026-06-01T12:00:00+00:00",
        "cache_create_time_utc_in_millis": 1780315200000,
    }
    client = make_client(monkeypatch, service)

    response = client.put("/ai/v1/chat/football/cache", headers={"User-Id": "user-1"})

    assert response.status_code == 200
    assert_success_response(response, {
        "cache_create_time": "2026-06-01T12:00:00+00:00",
        "cache_create_time_utc_in_millis": 1780315200000,
    })
    service.refresh_cache.assert_called_once_with(user_id="user-1")


def test_refresh_chat_football_cache_rejects_user_id_in_body(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.put(
        "/ai/v1/chat/football/cache",
        json={"user_id": "body-user"},
        headers={"User-Id": "header-user"},
    )

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.refresh_cache.assert_not_called()


def test_refresh_chat_football_cache_returns_422_without_user_id(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.put("/ai/v1/chat/football/cache")

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.refresh_cache.assert_not_called()
