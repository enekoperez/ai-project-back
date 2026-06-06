from types import SimpleNamespace
from unittest.mock import Mock

from webapp.repositories.chat_cache_repository import ChatCacheRepository


def test_chat_cache_repository_get_name_returns_cache(monkeypatch):
    chat_cache_model = Mock()
    chat_cache_model.objects.return_value.only.return_value.first.return_value = SimpleNamespace(name="cache-1")
    monkeypatch.setattr("webapp.repositories.chat_cache_repository.ChatCache", chat_cache_model)

    assert ChatCacheRepository().get_name(key={"user_id": "user-1"}) == "cache-1"
    chat_cache_model.objects.assert_called_once_with(key={"user_id": "user-1"})
    chat_cache_model.objects.return_value.only.assert_called_once_with("name")
    chat_cache_model.objects.return_value.only.return_value.first.assert_called_once_with()


def test_chat_cache_repository_get_name_returns_none_without_cache(monkeypatch):
    chat_cache_model = Mock()
    chat_cache_model.objects.return_value.only.return_value.first.return_value = None
    monkeypatch.setattr("webapp.repositories.chat_cache_repository.ChatCache", chat_cache_model)

    assert ChatCacheRepository().get_name(key={"user_id": "user-1"}) is None


def test_chat_cache_repository_upsert_name_delegates_to_model(monkeypatch):
    chat_cache_model = Mock()
    chat_cache_model.objects.return_value.update_one.return_value = 1
    monkeypatch.setattr("webapp.repositories.chat_cache_repository.ChatCache", chat_cache_model)

    assert ChatCacheRepository().upsert_name(key={"user_id": "user-1"}, name="cache-1") == 1
    chat_cache_model.objects.assert_called_once_with(key={"user_id": "user-1"})
    chat_cache_model.objects.return_value.update_one.assert_called_once_with(
        set__name="cache-1",
        upsert=True,
    )
