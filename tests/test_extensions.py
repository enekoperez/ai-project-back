from unittest.mock import Mock

from flask import Flask
from flask_limiter import Limiter

from webapp.api.chat_general_v1_api import chat_general_v1
from webapp.extensions import _rate_limit_key, limiter
from webapp.routes.error_handlers import init_error_handlers


def test_rate_limit_key_prefers_user_id_header():
    app = Flask(__name__)
    with app.test_request_context(headers={"User-Id": "user-42"}):
        assert _rate_limit_key() == "user-42"


def test_rate_limit_key_falls_back_to_client_ip():
    app = Flask(__name__)
    with app.test_request_context(environ_overrides={"REMOTE_ADDR": "203.0.113.7"}):
        assert _rate_limit_key() == "203.0.113.7"


def test_shared_chat_limit_blocks_after_ten_requests(monkeypatch):
    service = Mock()
    service.chat.return_value = {"id": "chat-1", "response": "ok", "created_at": "2026-06-01T12:00:00"}
    monkeypatch.setattr("webapp.api.chat_general_v1_api.chat_general_service", service)

    app = Flask(__name__)
    init_error_handlers(app)
    limiter.init_app(app)
    app.register_blueprint(chat_general_v1, url_prefix="/ai/v1/chat/general/")
    client = app.test_client()

    headers = {"User-Id": "chat-limit-user"}
    body = {"question": "hi"}
    statuses = [
        client.post("/ai/v1/chat/general/", json=body, headers=headers).status_code for _ in range(10)
    ]

    assert statuses.count(201) == 10
    blocked = client.post("/ai/v1/chat/general/", json=body, headers=headers)
    assert blocked.status_code == 429
    payload = blocked.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "too_many_requests"


def test_falls_back_to_in_memory_when_storage_unreachable(monkeypatch):
    service = Mock()
    service.chat.return_value = {"id": "chat-1", "response": "ok", "created_at": "2026-06-01T12:00:00"}
    monkeypatch.setattr("webapp.api.chat_general_v1_api.chat_general_service", service)

    # A limiter pointed at an unreachable backend with fallback enabled. The tight socket
    # timeouts make the failed connection give up immediately instead of stalling the test.
    fallback_limiter = Limiter(
        key_func=_rate_limit_key,
        storage_uri="redis://127.0.0.1:6399?socket_connect_timeout=0.05&socket_timeout=0.05",
        in_memory_fallback_enabled=True,
        application_limits=["3 per hour"],
    )
    app = Flask(__name__)
    init_error_handlers(app)
    fallback_limiter.init_app(app)
    app.register_blueprint(chat_general_v1, url_prefix="/ai/v1/chat/general/")
    client = app.test_client()

    headers = {"User-Id": "fallback-user"}
    body = {"question": "hi"}
    statuses = [
        client.post("/ai/v1/chat/general/", json=body, headers=headers).status_code for _ in range(4)
    ]

    # Storage is down, but requests are served (no 500) and still limited in memory.
    assert 500 not in statuses
    assert statuses.count(201) == 3
    assert statuses[-1] == 429
