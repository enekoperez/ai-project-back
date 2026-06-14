from unittest.mock import Mock

from webapp.repositories.chat_log_repository import ChatLogRepository


def test_chat_log_repository_create_delegates_to_model(monkeypatch):
    chat_log_model = Mock()
    chat_log_model.objects.create.return_value = "created-chat"
    monkeypatch.setattr("webapp.repositories.chat_log_repository.ChatLog", chat_log_model)

    assert ChatLogRepository().create(
        key={"user_id": "user-1"},
        user_question="What can this app do?",
        chat_api_response="Answer text",
    ) == "created-chat"
    chat_log_model.objects.create.assert_called_once_with(
        key={"user_id": "user-1"},
        user_question="What can this app do?",
        chat_api_response="Answer text",
    )


def test_chat_log_repository_get_chat_log_by_user_id_returns_log_when_owner(monkeypatch):
    log = Mock(key={"user_id": "user-1"})
    chat_log_model = Mock()
    chat_log_model.objects.return_value.only.return_value.first.return_value = log
    monkeypatch.setattr("webapp.repositories.chat_log_repository.ChatLog", chat_log_model)

    assert ChatLogRepository().get_chat_log_by_user_id(chat_log_id="chat-1", user_id="user-1") is log
    chat_log_model.objects.return_value.only.assert_called_once_with("key")


def test_chat_log_repository_get_chat_log_by_user_id_returns_none_when_wrong_user(monkeypatch):
    chat_log_model = Mock()
    chat_log_model.objects.return_value.only.return_value.first.return_value = Mock(key={"user_id": "other-user"})
    monkeypatch.setattr("webapp.repositories.chat_log_repository.ChatLog", chat_log_model)

    assert ChatLogRepository().get_chat_log_by_user_id(chat_log_id="chat-1", user_id="user-1") is None


def test_chat_log_repository_get_chat_log_by_user_id_returns_none_when_not_found(monkeypatch):
    chat_log_model = Mock()
    chat_log_model.objects.return_value.only.return_value.first.return_value = None
    monkeypatch.setattr("webapp.repositories.chat_log_repository.ChatLog", chat_log_model)

    assert ChatLogRepository().get_chat_log_by_user_id(chat_log_id="chat-1", user_id="user-1") is None


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


def test_chat_log_repository_get_history_returns_ordered_user_and_model_turns(monkeypatch):
    first_log = Mock(id="chat-1", user_question="Question 1", chat_api_response="Answer 1", created_at="date-1")
    second_log = Mock(id="chat-2", user_question="Question 2", chat_api_response="Answer 2", created_at="date-2")
    query = Mock()
    query.order_by.return_value.only.return_value.limit.return_value = [second_log, first_log]
    chat_log_model = Mock()
    chat_log_model.objects.return_value = query
    monkeypatch.setattr("webapp.repositories.chat_log_repository.ChatLog", chat_log_model)

    assert ChatLogRepository().get_history(key={"user_id": "user-1"}) == [
        {"chat_log_id": "chat-1", "role": "user", "text": "Question 1", "created_at": "date-1"},
        {"chat_log_id": "chat-1", "role": "model", "text": "Answer 1", "created_at": "date-1"},
        {"chat_log_id": "chat-2", "role": "user", "text": "Question 2", "created_at": "date-2"},
        {"chat_log_id": "chat-2", "role": "model", "text": "Answer 2", "created_at": "date-2"},
    ]
    chat_log_model.objects.assert_called_once()
    query.order_by.assert_called_once_with("-created_at")
    query.order_by.return_value.only.assert_called_once_with("user_question", "chat_api_response", "created_at")
    query.order_by.return_value.only.return_value.limit.assert_called_once_with(10)
