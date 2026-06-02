from webapp.services.base_chat_service import BaseChatService


def test_normalize_user_input_returns_string_for_string():
    service = BaseChatService()

    assert service._normalize_user_input("  hello  ") == "hello"


def test_normalize_user_input_returns_list_for_list():
    service = BaseChatService()

    assert service._normalize_user_input(["  first  ", "  second  "]) == [
        "first",
        "second",
    ]


def test_normalize_user_input_returns_empty_string_for_none():
    service = BaseChatService()

    assert service._normalize_user_input(None) == ""


def test_normalize_user_input_converts_non_string_scalar_to_string():
    service = BaseChatService()

    assert service._normalize_user_input(123) == "123"
