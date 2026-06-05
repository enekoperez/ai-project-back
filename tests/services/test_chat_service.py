from unittest.mock import Mock

from webapp.services.chat_service import ChatService


def test_like_delegates_to_repository():
    repository = Mock()
    repository.like.return_value = "liked-chat-log"
    service = ChatService()
    service.chat_log_repository = repository

    assert service.like(chat_log_id="chat-1") == "liked-chat-log"
    repository.like.assert_called_once_with(chat_log_id="chat-1")


def test_dislike_delegates_to_repository():
    repository = Mock()
    repository.dislike.return_value = "disliked-chat-log"
    service = ChatService()
    service.chat_log_repository = repository

    assert service.dislike(chat_log_id="chat-1") == "disliked-chat-log"
    repository.dislike.assert_called_once_with(chat_log_id="chat-1")
