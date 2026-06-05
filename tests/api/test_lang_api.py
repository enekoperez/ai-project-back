from unittest.mock import Mock

from flask import Flask

from webapp.api.lang_api import lang
from webapp.routes.error_handlers import init_error_handlers
from response_assertions import assert_error_code, assert_success_response


def make_client(monkeypatch, service):
    monkeypatch.setattr("webapp.api.lang_api.lang_service", service)

    app = Flask(__name__)
    init_error_handlers(app)
    app.register_blueprint(lang, url_prefix="/ai/lang/")
    return app.test_client()


def test_call_simple_returns_response(monkeypatch):
    service = Mock()
    service.call_simple.return_value = {"message": "Sunny"}
    client = make_client(monkeypatch, service)

    request_json = {"question": "What is the weather in Bilbao?"}
    response = client.post("/ai/lang/simple", json=request_json)

    assert response.status_code == 200
    assert_success_response(response, {"message": "Sunny"})
    service.call_simple.assert_called_once_with(request_json)


def test_call_simple_returns_422_without_question(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.post("/ai/lang/simple", json={})

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.call_simple.assert_not_called()


def test_call_complex_does_not_require_body(monkeypatch):
    service = Mock()
    service.call_complex.return_value = {"agent_response": [], "deep_agent_response": []}
    client = make_client(monkeypatch, service)

    response = client.post("/ai/lang/complex")

    assert response.status_code == 200
    assert_success_response(response, {"agent_response": [], "deep_agent_response": []})
    service.call_complex.assert_called_once_with()
