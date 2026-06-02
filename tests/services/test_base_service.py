import pytest

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
            chat_log_key={"user_id": "user-1"},
            system_prompt="system",
            user_prompt="user",
            is_chat=False,
            is_rag=False,
        )
