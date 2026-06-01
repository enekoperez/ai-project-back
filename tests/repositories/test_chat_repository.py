from unittest.mock import Mock

from webapp.repositories.chat_repository import ChatRepository


def test_chat_repository_create_delegates_to_model(monkeypatch):
    chat_model = Mock()
    chat_model.objects.create.return_value = "created-chat"
    monkeypatch.setattr("webapp.repositories.chat_repository.Chat", chat_model)

    assert ChatRepository().create() == "created-chat"
    chat_model.objects.create.assert_called_once_with()
