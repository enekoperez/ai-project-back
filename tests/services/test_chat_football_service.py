from datetime import datetime, timezone
from unittest.mock import Mock, patch

from webapp.prompts.chat_football_prompt import build_system_prompt, build_user_prompt
from webapp.services.base_service import BaseService
from webapp.services.chat_football_service import ChatFootballService


def test_chat_football_service_inherits_base_service():
    assert isinstance(ChatFootballService(), BaseService)


def test_chat_football_uses_chat_without_tools_and_separate_history():
    ai_service = Mock()
    ai_service.call_llm.return_value = (
        "Football teams have eleven players.",
        "model",
        1.0,
        None,
        [],
        100,
    )
    ai_service.google_get_cache.return_value = (None, None)
    chat_log_repository = Mock()
    created_at = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    ai_service.google_set_cache.return_value = ("cache-1", created_at)
    chat_log_repository.create.return_value = Mock(id="chat-1", created_at=created_at)
    chat_log_repository.get_history.return_value = []
    service = ChatFootballService()
    service.ai_service = ai_service
    service.chat_log_repository = chat_log_repository
    service.doc_service = Mock()
    service.doc_service.get_source_files.return_value = [
        {
            "source_name": "football.md",
            "path": "football-path",
        }
    ]
    service.doc_service.get_source_text.return_value = "A standard football team has eleven players."

    with patch("webapp.services.chat_football_service.time.sleep") as sleep:
        response = service.chat(
            user_id="user-1",
            request_json={"question": "  How many players are on a football team?  "},
        )

    assert response == {
        "chat_log_id": "chat-1",
        "chat_api_response": "Football teams have eleven players.",
        "date": "2026-06-01T12:00:00+00:00",
        "date_utc_in_millis": BaseService._to_millis(created_at),
        "cache_create_time": "2026-06-01T12:00:00+00:00",
        "cache_create_time_utc_in_millis": BaseService._to_millis(created_at),
        "source_names_and_scores": [],
    }
    chat_log_repository.get_history.assert_called_once_with(key={"user_id": "user-1", "key_2": "chat_football"})
    chat_log_repository.create.assert_called_once_with(
        key={"user_id": "user-1", "key_2": "chat_football"},
        user_question="How many players are on a football team?",
        chat_api_response="Football teams have eleven players.",
    )
    ai_service.google_get_cache.assert_called_once_with(display_name='{"user_id": "user-1", "key_2": "chat_football"}')
    sleep.assert_called_once_with(15)
    ai_service.google_set_cache.assert_called_once_with(
        display_name='{"user_id": "user-1", "key_2": "chat_football"}',
        system_instruction=build_system_prompt(football_data="A standard football team has eleven players."),
    )
    service.doc_service.get_source_files.assert_called_once_with()
    service.doc_service.get_source_text.assert_called_once_with(
        {
            "source_name": "football.md",
            "path": "football-path",
        }
    )
    ai_service.call_llm.assert_called_once_with(
        system_prompt=build_system_prompt(football_data="A standard football team has eleven players."),
        user_prompt=build_user_prompt(question="How many players are on a football team?"),
        max_output_tokens=6666,
        is_chat=True,
        is_rag=False,
        history=[],
        tool_declarations=None,
        tool_dispatch=None,
        cache_name="cache-1",
    )


def test_chat_football_reuses_existing_cache_without_loading_football_doc():
    ai_service = Mock()
    ai_service.google_get_cache.return_value = ("cache-1", datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc))
    ai_service.call_llm.return_value = ("Cached answer", "model", 1.0, None, [], 100)
    chat_log_repository = Mock()
    chat_log_repository.create.return_value = Mock(id="chat-1", created_at=None)
    chat_log_repository.get_history.return_value = []
    service = ChatFootballService()
    service.ai_service = ai_service
    service.chat_log_repository = chat_log_repository
    service.doc_service = Mock()

    response = service.chat(user_id="user-1", request_json={"question": "Who plays?"})

    assert response["chat_api_response"] == "Cached answer"
    service.doc_service.get_source_files.assert_not_called()
    service.doc_service.get_source_text.assert_not_called()
    ai_service.google_set_cache.assert_not_called()
    ai_service.call_llm.assert_called_once_with(
        system_prompt=None,
        user_prompt=build_user_prompt(question="Who plays?"),
        max_output_tokens=6666,
        is_chat=True,
        is_rag=False,
        history=[],
        tool_declarations=None,
        tool_dispatch=None,
        cache_name="cache-1",
    )


def test_chat_football_get_cache_returns_cache_create_time():
    created_at = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    service = ChatFootballService()
    service.ai_service = Mock()
    service.ai_service.google_get_cache.return_value = ("cache-1", created_at)

    assert service.get_cache(user_id="user-1") == {
        "cache_create_time": "2026-06-01T12:00:00+00:00",
        "cache_create_time_utc_in_millis": BaseService._to_millis(created_at),
    }
    service.ai_service.google_get_cache.assert_called_once_with(
        display_name='{"user_id": "user-1", "key_2": "chat_football"}'
    )


def test_chat_football_refresh_cache_deletes_and_recreates_cache():
    created_at = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    service = ChatFootballService()
    service.ai_service = Mock()
    service.ai_service.google_set_cache.return_value = ("cache-1", created_at)
    service.doc_service = Mock()
    service.doc_service.get_source_files.return_value = []

    with patch("webapp.services.chat_football_service.time.sleep") as sleep:
        assert service.refresh_cache(user_id="user-1") == {
            "cache_create_time": "2026-06-01T12:00:00+00:00",
            "cache_create_time_utc_in_millis": BaseService._to_millis(created_at),
        }

    display_name = '{"user_id": "user-1", "key_2": "chat_football"}'
    service.ai_service.google_delete_cache.assert_called_once_with(display_name=display_name)
    sleep.assert_called_once_with(15)
    service.ai_service.google_set_cache.assert_called_once_with(
        display_name=display_name,
        system_instruction=build_system_prompt(football_data=""),
    )


def test_chat_football_get_chat_returns_football_history():
    created_at = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    service = ChatFootballService()
    service.chat_log_repository = Mock()
    service.chat_log_repository.get_history.return_value = [
        {"role": "user", "text": "Who won?", "created_at": created_at},
        {"role": "model", "text": '"Real Madrid"', "created_at": created_at},
    ]

    assert service.get_chat(user_id="user-1") == [
        {
            "role": "user",
            "text": "Who won?",
            "created_at": "2026-06-01T12:00:00+00:00",
            "created_at_utc_in_millis": BaseService._to_millis(created_at),
        },
        {
            "role": "model",
            "text": "Real Madrid",
            "created_at": "2026-06-01T12:00:00+00:00",
            "created_at_utc_in_millis": BaseService._to_millis(created_at),
        },
    ]
    service.chat_log_repository.get_history.assert_called_once_with(
        key={"user_id": "user-1", "key_2": "chat_football"}
    )
