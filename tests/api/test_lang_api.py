from unittest.mock import Mock

from flask import Flask

from webapp.api.lang_api import lang


def make_client(monkeypatch, service):
    monkeypatch.setattr("webapp.api.lang_api.lang_service", service)

    app = Flask(__name__)
    app.register_blueprint(lang, url_prefix="/ai/lang/")
    return app.test_client()


def test_lang_simple_post_returns_response(monkeypatch):
    service = Mock()
    service.call_simple.return_value = {"message": "Hello world from SIMPLE"}
    client = make_client(monkeypatch, service)

    request_json = {"question": "What's the weather in San Francisco?"}
    response = client.post("/ai/lang/simple", json=request_json)

    assert response.status_code == 200
    assert response.get_json() == {"message": "Hello world from SIMPLE"}
    service.call_simple.assert_called_once_with(request_json)


def test_lang_complex_post_returns_response(monkeypatch):
    service = Mock()
    service.call_complex.return_value = {"message": "Hello world from COMPLEX"}
    client = make_client(monkeypatch, service)

    response = client.post("/ai/lang/complex")

    assert response.status_code == 200
    assert response.get_json() == {"message": "Hello world from COMPLEX"}
    service.call_complex.assert_called_once_with()


def test_get_lang_simple_is_not_available(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get("/ai/lang/simple")

    assert response.status_code == 405
    service.call_simple.assert_not_called()


def test_get_lang_complex_is_not_available(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get("/ai/lang/complex")

    assert response.status_code == 405
    service.call_complex.assert_not_called()
