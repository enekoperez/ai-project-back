from unittest.mock import Mock

from webapp.repositories.chat_log_repository import ChatLogRepository


def test_chat_log_repository_create_delegates_to_model(monkeypatch):
    chat_log_model = Mock()
    chat_log_model.objects.create.return_value = "created-chat"
    monkeypatch.setattr("webapp.repositories.chat_log_repository.ChatLog", chat_log_model)

    assert ChatLogRepository().create() == "created-chat"
    chat_log_model.objects.create.assert_called_once_with()
