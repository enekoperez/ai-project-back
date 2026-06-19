from unittest.mock import Mock

from flask import Flask

from response_assertions import assert_error_code, assert_success_response
from webapp.api.ocr_v1_api import ocr_v1
from webapp.config import Config
from webapp.routes.error_handlers import init_error_handlers


def make_client(monkeypatch, service):
    monkeypatch.setattr("webapp.api.ocr_v1_api.ocr_service", service)

    app = Flask(__name__)
    init_error_handlers(app)
    app.register_blueprint(ocr_v1, url_prefix="/ai/v1/ocr/")
    return app.test_client()


def test_ask_ocr_questions_returns_response(monkeypatch):
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
    response = client.post("/ai/v1/ocr/", json=request_json)

    assert response.status_code == 201
    assert_success_response(response, {
        "id": "ocr-1",
        "response": "The invoice total is 120.00.",
        "created_at": "2026-06-01T12:00:00",
    })
    service.ask.assert_called_once_with(request_json)


def test_answer_ocr_questions_returns_422_without_file_url(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.post("/ai/v1/ocr/", json={"questions": ["What is the total?"]})

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.ask.assert_not_called()


def test_answer_ocr_questions_returns_422_with_empty_questions(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.post("/ai/v1/ocr/", json={"file_url": "https://example.com/invoice.pdf", "questions": []})

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.ask.assert_not_called()


def test_answer_ocr_questions_returns_422_with_blank_question(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.post("/ai/v1/ocr/", json={"file_url": "https://example.com/invoice.pdf", "questions": [" "]})

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.ask.assert_not_called()


def test_answer_ocr_questions_returns_422_with_too_many_questions(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.post(
        "/ai/v1/ocr/",
        json={"file_url": "https://example.com/invoice.pdf", "questions": [f"Q{i}?" for i in range(11)]},
    )

    assert response.status_code == 422
    assert_error_code(response, "validation_error")
    service.ask.assert_not_called()


def test_oversized_body_is_rejected_with_413(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)
    assert Config.MAX_CONTENT_LENGTH == 1 * 1024 * 1024
    client.application.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH

    oversized = b'{"file_url":"' + b"a" * Config.MAX_CONTENT_LENGTH + b'"}'
    response = client.post("/ai/v1/ocr/", data=oversized, content_type="application/json")

    assert response.status_code == 413
    assert_error_code(response, "request_entity_too_large")
    service.ask.assert_not_called()


def test_get_ocr_is_not_available(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get("/ai/v1/ocr/")

    assert response.status_code == 405
    assert_error_code(response, "method_not_allowed")
    service.ask.assert_not_called()
