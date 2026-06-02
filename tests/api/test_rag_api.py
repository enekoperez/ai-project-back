from unittest.mock import Mock

from flask import Flask

from webapp.api.rag_api import rag


def make_client(monkeypatch, service):
    monkeypatch.setattr("webapp.api.rag_api.rag_service", service)

    app = Flask(__name__)
    app.register_blueprint(rag, url_prefix="/ai/rag/")
    return app.test_client()


def test_sync_rag_returns_sync_status(monkeypatch):
    service = Mock()
    service.sync.return_value = True
    client = make_client(monkeypatch, service)

    response = client.post("/ai/rag/sync")

    assert response.status_code == 200
    assert response.get_json() == {"synced": True}
    service.sync.assert_called_once_with()


def test_get_rag_sync_is_not_available(monkeypatch):
    service = Mock()
    client = make_client(monkeypatch, service)

    response = client.get("/ai/rag/sync")

    assert response.status_code == 405
    service.sync.assert_not_called()
