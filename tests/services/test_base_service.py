import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from webapp.services.base_service import BaseService


def test_normalize_user_input_returns_string_for_string():
    service = BaseService()

    assert service._normalize_user_input("  hello  ") == "hello"


def test_normalize_user_input_returns_list_for_list():
    service = BaseService()

    assert service._normalize_user_input(["  first  ", "  second  "]) == [
        "first",
        "second",
    ]


def test_normalize_user_input_returns_empty_string_for_none():
    service = BaseService()

    assert service._normalize_user_input(None) == ""


def test_normalize_user_input_converts_non_string_scalar_to_string():
    service = BaseService()

    assert service._normalize_user_input(123) == "123"


def test_key_and_display_name_uses_user_id_only():
    chat_log_key, display_name = BaseService._create_chat_log_key_and_display_name(user_id="user-1")

    assert chat_log_key == {"user_id": "user-1"}
    assert display_name == '{"user_id": "user-1"}'


def test_key_and_display_name_includes_second_key_when_present():
    chat_log_key, display_name = BaseService._create_chat_log_key_and_display_name(user_id="user-1", key_2="thread-1")

    assert chat_log_key == {"user_id": "user-1", "key_2": "thread-1"}
    assert display_name == '{"user_id": "user-1", "key_2": "thread-1"}'


def test_call_llm_and_log_rejects_chat_and_rag_together():
    service = BaseService.__new__(BaseService)

    with pytest.raises(ValueError, match="Exactly one of is_chat or is_rag must be true."):
        service._call_llm_and_log(
            user_question="question",
            chat_log_key={"user_id": "user-1"},
            system_prompt="system",
            user_prompt="user",
            is_chat=True,
            is_rag=True,
        )


def test_call_llm_and_log_rejects_missing_chat_and_rag_mode():
    service = BaseService.__new__(BaseService)

    with pytest.raises(ValueError, match="Exactly one of is_chat or is_rag must be true."):
        service._call_llm_and_log(
            user_question="question",
            chat_log_key={"user_id": "user-1"},
            system_prompt="system",
            user_prompt="user",
            is_chat=False,
            is_rag=False,
        )


def test_get_chat_history_formats_dates_and_model_json():
    created_at = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    repository = Mock()
    repository.get_history.return_value = [
        {"chat_log_id": "chat-1", "role": "user", "text": "Question", "created_at": created_at},
        {"chat_log_id": "chat-1", "role": "model", "text": '{"answer": "Answer"}', "created_at": created_at},
    ]
    service = BaseService.__new__(BaseService)
    service.chat_log_repository = repository

    assert service.get_chat_history(user_id="user-1", key_2="thread-1") == [
        {
            "chat_log_id": "chat-1",
            "role": "user",
            "text": "Question",
            "created_at": "2026-06-01T12:00:00+00:00",
            "created_at_utc_in_millis": BaseService._to_millis(created_at),
        },
        {
            "chat_log_id": "chat-1",
            "role": "model",
            "text": {"answer": "Answer"},
            "created_at": "2026-06-01T12:00:00+00:00",
            "created_at_utc_in_millis": BaseService._to_millis(created_at),
        },
    ]
    repository.get_history.assert_called_once_with(key={"user_id": "user-1", "key_2": "thread-1"})
