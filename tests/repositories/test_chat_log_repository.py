from unittest.mock import Mock

from webapp.repositories.chat_log_repository import ChatLogRepository


def test_chat_log_repository_create_delegates_to_model(monkeypatch):
    chat_log_model = Mock()
    chat_log_model.objects.create.return_value = "created-chat"
    monkeypatch.setattr("webapp.repositories.chat_log_repository.ChatLog", chat_log_model)

    assert ChatLogRepository().create(key={"user_id": "user-1"}) == "created-chat"
    chat_log_model.objects.create.assert_called_once_with(key={"user_id": "user-1"})


def test_chat_log_repository_like_sets_liked_and_clears_disliked(monkeypatch):
    chat_log_model = Mock()
    chat_log_model.objects.return_value.only.return_value.first.return_value = Mock(liked=False)
    monkeypatch.setattr("webapp.repositories.chat_log_repository.ChatLog", chat_log_model)

    assert ChatLogRepository().like(chat_log_id="chat-1") == {
        "chat_log_id": "chat-1",
        "liked": True,
        "disliked": None,
    }
    chat_log_model.objects.assert_any_call(id="chat-1")
    chat_log_model.objects.return_value.only.assert_called_once_with("liked")
    chat_log_model.objects.return_value.only.return_value.first.assert_called_once_with()
    chat_log_model.objects.return_value.update_one.assert_called_once_with(
        set__liked=True,
        set__disliked=None,
    )


def test_chat_log_repository_like_clears_existing_like(monkeypatch):
    chat_log_model = Mock()
    chat_log_model.objects.return_value.only.return_value.first.return_value = Mock(liked=True)
    monkeypatch.setattr("webapp.repositories.chat_log_repository.ChatLog", chat_log_model)

    assert ChatLogRepository().like(chat_log_id="chat-1") == {
        "chat_log_id": "chat-1",
        "liked": None,
        "disliked": None,
    }
    chat_log_model.objects.assert_any_call(id="chat-1")
    chat_log_model.objects.return_value.only.assert_called_once_with("liked")
    chat_log_model.objects.return_value.update_one.assert_called_once_with(
        set__liked=None,
    )


def test_chat_log_repository_dislike_sets_disliked_and_clears_liked(monkeypatch):
    chat_log_model = Mock()
    chat_log_model.objects.return_value.only.return_value.first.return_value = Mock(disliked=False)
    monkeypatch.setattr("webapp.repositories.chat_log_repository.ChatLog", chat_log_model)

    assert ChatLogRepository().dislike(chat_log_id="chat-1") == {
        "chat_log_id": "chat-1",
        "liked": None,
        "disliked": True,
    }
    chat_log_model.objects.assert_any_call(id="chat-1")
    chat_log_model.objects.return_value.only.assert_called_once_with("disliked")
    chat_log_model.objects.return_value.only.return_value.first.assert_called_once_with()
    chat_log_model.objects.return_value.update_one.assert_called_once_with(
        set__disliked=True,
        set__liked=None,
    )


def test_chat_log_repository_dislike_clears_existing_dislike(monkeypatch):
    chat_log_model = Mock()
    chat_log_model.objects.return_value.only.return_value.first.return_value = Mock(disliked=True)
    monkeypatch.setattr("webapp.repositories.chat_log_repository.ChatLog", chat_log_model)

    assert ChatLogRepository().dislike(chat_log_id="chat-1") == {
        "chat_log_id": "chat-1",
        "liked": None,
        "disliked": None,
    }
    chat_log_model.objects.assert_any_call(id="chat-1")
    chat_log_model.objects.return_value.only.assert_called_once_with("disliked")
    chat_log_model.objects.return_value.update_one.assert_called_once_with(
        set__disliked=None,
    )
