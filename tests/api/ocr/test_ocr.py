from unittest.mock import Mock

from flask import Flask

from webapp.api.ocr import ocr


def make_client(monkeypatch, service):
    monkeypatch.setattr("webapp.api.ocr.ocr_service", service)

    app = Flask(__name__)
    app.register_blueprint(ocr, url_prefix="/ai/ocr/")
    return app.test_client()


def test_create_ocr_returns_created_ocr(monkeypatch):
    service = Mock()
    service.create.return_value = {
        "id": "ocr-1",
        "created_at": "2026-06-01T12:00:00",
    }
    client = make_client(monkeypatch, service)

    response = client.post("/ai/ocr/")

    assert response.status_code == 201
    assert response.get_json() == {
        "id": "ocr-1",
        "created_at": "2026-06-01T12:00:00",
    }
    service.create.assert_called_once_with()
    service.get_all.assert_not_called()


def test_get_ocrs_returns_all_ocrs(monkeypatch):
    service = Mock()
    service.get_all.return_value = [
        {"id": "ocr-2", "created_at": "2026-06-01T12:01:00"},
        {"id": "ocr-1", "created_at": "2026-06-01T12:00:00"},
    ]
    client = make_client(monkeypatch, service)

    response = client.get("/ai/ocr/")

    assert response.status_code == 200
    assert response.get_json() == [
        {"id": "ocr-2", "created_at": "2026-06-01T12:01:00"},
        {"id": "ocr-1", "created_at": "2026-06-01T12:00:00"},
    ]
    service.get_all.assert_called_once_with()
    service.create.assert_not_called()
