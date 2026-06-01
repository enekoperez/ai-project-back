from unittest.mock import Mock

from flask import Flask

from webapp.api.chat_api import chat


def make_client(monkeypatch, service):
    monkeypatch.setattr("webapp.api.chat_api.chat_service", service)

    app = Flask(__name__)
    app.register_blueprint(chat, url_prefix="/ai/chat/")
    return app.test_client()


def test_create_chat_returns_created_chat(monkeypatch):
    service = Mock()
    service.create.return_value = {
        "id": "chat-1",
        "created_at": "2026-06-01T12:00:00",
    }
    client = make_client(monkeypatch, service)

    response = client.post("/ai/chat/")

    assert response.status_code == 201
    assert response.get_json() == {
        "id": "chat-1",
        "created_at": "2026-06-01T12:00:00",
    }
    service.create.assert_called_once_with()
    service.get_all.assert_not_called()


def test_get_chats_returns_all_chats(monkeypatch):
    service = Mock()
    service.get_all.return_value = [
        {"id": "chat-2", "created_at": "2026-06-01T12:01:00"},
        {"id": "chat-1", "created_at": "2026-06-01T12:00:00"},
    ]
    client = make_client(monkeypatch, service)

    response = client.get("/ai/chat/")

    assert response.status_code == 200
    assert response.get_json() == [
        {"id": "chat-2", "created_at": "2026-06-01T12:01:00"},
        {"id": "chat-1", "created_at": "2026-06-01T12:00:00"},
    ]
    service.get_all.assert_called_once_with()
    service.create.assert_not_called()
