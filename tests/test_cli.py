from unittest.mock import Mock

from flask import Flask

from webapp.cli import init_cli


def test_init_cli_registers_rag_sync_command(monkeypatch):
    rag_service = Mock()
    rag_service.sync.return_value = True
    rag_service_factory = Mock(return_value=rag_service)
    monkeypatch.setattr("webapp.cli.RagService", rag_service_factory)
    app = Flask(__name__)

    init_cli(app)
    result = app.test_cli_runner().invoke(args=["rag-sync"])

    assert result.exit_code == 0
    rag_service_factory.assert_called_once_with()
    rag_service.sync.assert_called_once_with()
