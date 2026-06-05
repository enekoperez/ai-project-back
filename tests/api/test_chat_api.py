from unittest.mock import Mock

from flask import Flask

from webapp.api.chat_api import chat
from webapp.api.chat_football_api import chat_football
from webapp.api.chat_general_api import chat_general
from webapp.api.chat_weather_api import chat_weather
from webapp.routes.error_handlers import init_error_handlers


def make_client(monkeypatch, service, chat_general_service=None, chat_weather_service=None, chat_football_service=None):
    monkeypatch.setattr("webapp.api.chat_api.chat_service", service)
    monkeypatch.setattr("webapp.api.chat_general_api.chat_general_service", chat_general_service or service)
    monkeypatch.setattr("webapp.api.chat_weather_api.chat_weather_service", chat_weather_service or service)
    monkeypatch.setattr("webapp.api.chat_football_api.chat_football_service", chat_football_service or service)

    app = Flask(__name__)
    init_error_handlers(app)
    app.register_blueprint(chat, url_prefix="/ai/chat/")
    app.register_blueprint(chat_general, url_prefix="/ai/chat/general/")
    app.register_blueprint(chat_football, url_prefix="/ai/chat/football/")
    app.register_blueprint(chat_weather, url_prefix="/ai/chat/weather/")
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
    response = client.post("/ai/chat/general/", json=request_json)

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
    response = client.post("/ai/chat/general/", json=request_json, headers={"User-Id": "header-user"})

    assert response.status_code == 200
    assert response.get_json() == {"chat_log_id": "chat-1"}
    service.chat.assert_called_once_with("header-user", request_json)


def test_answer_chat_question_returns_422_without_question(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.post("/ai/chat/general/", json={"user_id": "user-1"})

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "validation_error"
    service.chat.assert_not_called()


def test_answer_chat_question_returns_422_without_user_id(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.post("/ai/chat/general/", json={"question": "How do I extract invoice totals?"})

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "validation_error"
    service.chat.assert_not_called()


def test_chat_weather_question_returns_response(monkeypatch):
    service = Mock()
    service.chat.return_value = {"chat_log_id": "chat-1", "chat_api_response": "Bad weather in Bilbao."}
    client = make_client(monkeypatch, service)

    request_json = {"user_id": "user-1", "question": "What's the weather in Bilbao?"}
    response = client.post("/ai/chat/weather/", json=request_json)

    assert response.status_code == 200
    assert response.get_json() == {"chat_log_id": "chat-1", "chat_api_response": "Bad weather in Bilbao."}
    service.chat.assert_called_once_with("user-1", request_json)


def test_chat_weather_uses_user_id_header(monkeypatch):
    service = Mock()
    service.chat.return_value = {"chat_log_id": "chat-1"}
    client = make_client(monkeypatch, service)

    request_json = {"user_id": "body-user", "question": "What's the weather in Oviedo?"}
    response = client.post("/ai/chat/weather/", json=request_json, headers={"User-Id": "header-user"})

    assert response.status_code == 200
    assert response.get_json() == {"chat_log_id": "chat-1"}
    service.chat.assert_called_once_with("header-user", request_json)


def test_chat_weather_returns_422_for_empty_question(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.post("/ai/chat/weather/", json={"user_id": "user-1", "question": " "})

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "validation_error"
    service.chat.assert_not_called()


def test_get_chat_weather_returns_history_from_body_user_id(monkeypatch):
    service = Mock()
    service.get_chat.return_value = [{"chat_log_id": "chat-1", "role": "user", "text": "Weather?"}]
    client = make_client(monkeypatch, Mock(), chat_weather_service=service)

    response = client.get("/ai/chat/weather/", json={"user_id": "user-1"})

    assert response.status_code == 200
    assert response.get_json() == [{"chat_log_id": "chat-1", "role": "user", "text": "Weather?"}]
    service.get_chat.assert_called_once_with(user_id="user-1")


def test_get_chat_weather_uses_user_id_header(monkeypatch):
    service = Mock()
    service.get_chat.return_value = []
    client = make_client(monkeypatch, Mock(), chat_weather_service=service)

    response = client.get("/ai/chat/weather/", json={"user_id": "body-user"}, headers={"User-Id": "header-user"})

    assert response.status_code == 200
    assert response.get_json() == []
    service.get_chat.assert_called_once_with(user_id="header-user")


def test_get_chat_weather_returns_422_without_user_id(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, Mock(), chat_weather_service=service)

    response = client.get("/ai/chat/weather/")

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "validation_error"
    service.get_chat.assert_not_called()


def test_chat_football_question_returns_response(monkeypatch):
    service = Mock()
    service.chat.return_value = {"chat_log_id": "chat-1", "chat_api_response": "Football teams have eleven players."}
    client = make_client(monkeypatch, service)

    request_json = {"user_id": "user-1", "question": "How many players are on a football team?"}
    response = client.post("/ai/chat/football/", json=request_json)

    assert response.status_code == 200
    assert response.get_json() == {"chat_log_id": "chat-1", "chat_api_response": "Football teams have eleven players."}
    service.chat.assert_called_once_with("user-1", request_json)


def test_chat_football_uses_user_id_header(monkeypatch):
    service = Mock()
    service.chat.return_value = {"chat_log_id": "chat-1"}
    client = make_client(monkeypatch, service)

    request_json = {"user_id": "body-user", "question": "Who won?"}
    response = client.post("/ai/chat/football/", json=request_json, headers={"User-Id": "header-user"})

    assert response.status_code == 200
    assert response.get_json() == {"chat_log_id": "chat-1"}
    service.chat.assert_called_once_with("header-user", request_json)


def test_chat_football_returns_422_without_json(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.post("/ai/chat/football/")

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "validation_error"
    service.chat.assert_not_called()


def test_get_chat_football_returns_history_from_body_user_id(monkeypatch):
    service = Mock()
    service.get_chat.return_value = [{"chat_log_id": "chat-1", "role": "user", "text": "Who won?"}]
    client = make_client(monkeypatch, Mock(), chat_football_service=service)

    response = client.get("/ai/chat/football/", json={"user_id": "user-1"})

    assert response.status_code == 200
    assert response.get_json() == [{"chat_log_id": "chat-1", "role": "user", "text": "Who won?"}]
    service.get_chat.assert_called_once_with(user_id="user-1")


def test_get_chat_football_uses_user_id_header(monkeypatch):
    service = Mock()
    service.get_chat.return_value = []
    client = make_client(monkeypatch, Mock(), chat_football_service=service)

    response = client.get("/ai/chat/football/", json={"user_id": "body-user"}, headers={"User-Id": "header-user"})

    assert response.status_code == 200
    assert response.get_json() == []
    service.get_chat.assert_called_once_with(user_id="header-user")


def test_get_chat_football_returns_422_without_user_id(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, Mock(), chat_football_service=service)

    response = client.get("/ai/chat/football/")

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "validation_error"
    service.get_chat.assert_not_called()


def test_get_chat_football_cache_returns_cache_create_time(monkeypatch):
    service = Mock()
    service.get_cache.return_value = {
        "cache_create_time": "2026-06-01T12:00:00+00:00",
        "cache_create_time_utc_in_millis": 1780315200000,
    }
    client = make_client(monkeypatch, Mock(), chat_football_service=service)

    response = client.get("/ai/chat/football/cache", json={"user_id": "user-1"})

    assert response.status_code == 200
    assert response.get_json() == {
        "cache_create_time": "2026-06-01T12:00:00+00:00",
        "cache_create_time_utc_in_millis": 1780315200000,
    }
    service.get_cache.assert_called_once_with(user_id="user-1")


def test_get_chat_football_cache_uses_user_id_header(monkeypatch):
    service = Mock()
    service.get_cache.return_value = {
        "cache_create_time": None,
        "cache_create_time_utc_in_millis": None,
    }
    client = make_client(monkeypatch, Mock(), chat_football_service=service)

    response = client.get(
        "/ai/chat/football/cache",
        json={"user_id": "body-user"},
        headers={"User-Id": "header-user"},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "cache_create_time": None,
        "cache_create_time_utc_in_millis": None,
    }
    service.get_cache.assert_called_once_with(user_id="header-user")


def test_get_chat_football_cache_returns_422_without_user_id(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, Mock(), chat_football_service=service)

    response = client.get("/ai/chat/football/cache")

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "validation_error"
    service.get_cache.assert_not_called()


def test_refresh_chat_football_cache_returns_cache_create_time(monkeypatch):
    service = Mock()
    service.refresh_cache.return_value = {
        "cache_create_time": "2026-06-01T12:00:00+00:00",
        "cache_create_time_utc_in_millis": 1780315200000,
    }
    client = make_client(monkeypatch, Mock(), chat_football_service=service)

    response = client.put("/ai/chat/football/cache", json={"user_id": "user-1"})

    assert response.status_code == 200
    assert response.get_json() == {
        "cache_create_time": "2026-06-01T12:00:00+00:00",
        "cache_create_time_utc_in_millis": 1780315200000,
    }
    service.refresh_cache.assert_called_once_with(user_id="user-1")


def test_refresh_chat_football_cache_uses_user_id_header(monkeypatch):
    service = Mock()
    service.refresh_cache.return_value = {
        "cache_create_time": "2026-06-01T12:00:00+00:00",
        "cache_create_time_utc_in_millis": 1780315200000,
    }
    client = make_client(monkeypatch, Mock(), chat_football_service=service)

    response = client.put(
        "/ai/chat/football/cache",
        json={"user_id": "body-user"},
        headers={"User-Id": "header-user"},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "cache_create_time": "2026-06-01T12:00:00+00:00",
        "cache_create_time_utc_in_millis": 1780315200000,
    }
    service.refresh_cache.assert_called_once_with(user_id="header-user")


def test_refresh_chat_football_cache_returns_422_without_user_id(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, Mock(), chat_football_service=service)

    response = client.put("/ai/chat/football/cache")

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "validation_error"
    service.refresh_cache.assert_not_called()


def test_get_chat_returns_history_from_body_user_id(monkeypatch):
    service = Mock()
    service.get_chat.return_value = [{"chat_log_id": "chat-1", "role": "user", "text": "Question"}]
    client = make_client(monkeypatch, service)

    response = client.get("/ai/chat/general/", json={"user_id": "user-1"})

    assert response.status_code == 200
    assert response.get_json() == [{"chat_log_id": "chat-1", "role": "user", "text": "Question"}]
    service.get_chat.assert_called_once_with(user_id="user-1")


def test_get_chat_uses_user_id_header(monkeypatch):
    service = Mock()
    service.get_chat.return_value = []
    client = make_client(monkeypatch, service)

    response = client.get("/ai/chat/general/", json={"user_id": "body-user"}, headers={"User-Id": "header-user"})

    assert response.status_code == 200
    assert response.get_json() == []
    service.get_chat.assert_called_once_with(user_id="header-user")


def test_get_chat_returns_422_without_user_id(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get("/ai/chat/general/")

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "validation_error"
    service.get_chat.assert_not_called()


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


def test_like_chat_log_returns_422_for_blank_path_id(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.post("/ai/chat/%20/like")

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "validation_error"
    service.like.assert_not_called()


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




