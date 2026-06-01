from unittest.mock import Mock

from flask import Flask

from webapp.api.ocr_api import ocr


def make_client(monkeypatch, service):
    monkeypatch.setattr("webapp.api.ocr_api.ocr_service", service)

    app = Flask(__name__)
    app.register_blueprint(ocr, url_prefix="/ai/ocr/")
    return app.test_client()


def test_answer_ocr_questions_returns_response(monkeypatch):
    service = Mock()
    service.ask.return_value = {
        "id": "ocr-1",
        "response": "The invoice total is 120.00.",
        "created_at": "2026-06-01T12:00:00",
    }
    client = make_client(monkeypatch, service)

    request_json = {
        "file_url": "https://example.com/invoice.pdf",
        "questions": ["What is the total?"],
    }
    response = client.post("/ai/ocr/", json=request_json)

    assert response.status_code == 200
    assert response.get_json() == {
        "id": "ocr-1",
        "response": "The invoice total is 120.00.",
        "created_at": "2026-06-01T12:00:00",
    }
    service.ask.assert_called_once_with(request_json)


def test_get_ocr_is_not_available(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get("/ai/ocr/")

    assert response.status_code == 405
    service.ask.assert_not_called()
