import pytest
from unittest.mock import Mock
from werkzeug.exceptions import Forbidden

from webapp.services.chat_service import ChatService


def test_chat_service_raise_if_not_owner_passes_when_owner():
    repository = Mock()
    repository.get_chat_log_by_user_id.return_value = Mock()
    service = ChatService()
    service.chat_log_repository = repository

    service._raise_if_not_owner(chat_log_id="chat-1", user_id="user-1")
    repository.get_chat_log_by_user_id.assert_called_once_with("chat-1", "user-1")


def test_chat_service_raise_if_not_owner_raises_forbidden_when_not_owner():
    repository = Mock()
    repository.get_chat_log_by_user_id.return_value = None
    service = ChatService()
    service.chat_log_repository = repository

    with pytest.raises(Forbidden):
        service._raise_if_not_owner(chat_log_id="chat-1", user_id="user-1")


def test_chat_service_like_delegates_to_repository():
    repository = Mock()
    repository.get_chat_log_by_user_id.return_value = Mock()
    repository.like.return_value = {"chat_log_id": "chat-1", "liked": True, "disliked": None}
    service = ChatService()
    service.chat_log_repository = repository

    assert service.like(chat_log_id="chat-1", user_id="user-1") == {
        "chat_log_id": "chat-1",
        "liked": True,
        "disliked": None,
    }
    repository.get_chat_log_by_user_id.assert_called_once_with("chat-1", "user-1")
    repository.like.assert_called_once_with(chat_log_id="chat-1")


def test_chat_service_like_raises_forbidden_when_not_owner():
    repository = Mock()
    repository.get_chat_log_by_user_id.return_value = None
    service = ChatService()
    service.chat_log_repository = repository

    with pytest.raises(Forbidden):
        service.like(chat_log_id="chat-1", user_id="user-1")
    repository.like.assert_not_called()


def test_chat_service_dislike_delegates_to_repository():
    repository = Mock()
    repository.get_chat_log_by_user_id.return_value = Mock()
    repository.dislike.return_value = {"chat_log_id": "chat-1", "liked": None, "disliked": True}
    service = ChatService()
    service.chat_log_repository = repository

    assert service.dislike(chat_log_id="chat-1", user_id="user-1") == {
        "chat_log_id": "chat-1",
        "liked": None,
        "disliked": True,
    }
    repository.get_chat_log_by_user_id.assert_called_once_with("chat-1", "user-1")
    repository.dislike.assert_called_once_with(chat_log_id="chat-1")


def test_chat_service_dislike_raises_forbidden_when_not_owner():
    repository = Mock()
    repository.get_chat_log_by_user_id.return_value = None
    service = ChatService()
    service.chat_log_repository = repository

    with pytest.raises(Forbidden):
        service.dislike(chat_log_id="chat-1", user_id="user-1")
    repository.dislike.assert_not_called()
