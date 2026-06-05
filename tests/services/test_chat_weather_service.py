from datetime import datetime, timezone
from unittest.mock import Mock

from webapp.prompts.chat_weather_prompt import build_system_prompt, build_user_prompt
from webapp.services.base_service import BaseService
from webapp.services.chat_weather_service import ChatWeatherService
from webapp.tools.chat_weather_tools import ChatWeatherTools


def test_chat_weather_service_inherits_base_service():
    assert isinstance(ChatWeatherService(), BaseService)


def test_chat_weather_uses_tools_without_rag_and_separate_history():
    ai_service = Mock()
    ai_service.call_llm.return_value = (
        "The weather in Bilbao is bad.",
        "model",
        1.0,
        None,
        [{"name": "get_weather", "args": {"city": "Bilbao"}}],
        100,
    )
    chat_log_repository = Mock()
    created_at = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    chat_log_repository.create.return_value = Mock(id="chat-1", created_at=created_at)
    chat_log_repository.get_history.return_value = []
    service = ChatWeatherService()
    service.ai_service = ai_service
    service.chat_log_repository = chat_log_repository

    response = service.chat(
        user_id="user-1",
        request_json={"question": "  What's the weather in Bilbao?  "},
    )

    assert response == {
        "chat_log_id": "chat-1",
        "chat_api_response": "The weather in Bilbao is bad.",
        "date": "2026-06-01T12:00:00+00:00",
        "date_utc_in_millis": BaseService._to_millis(created_at),
        "cache_create_time": None,
        "cache_create_time_utc_in_millis": None,
        "source_names_and_scores": [],
    }
    chat_log_repository.get_history.assert_called_once_with(key={"user_id": "user-1", "key_2": "chat_weather"})
    chat_log_repository.create.assert_called_once_with(
        key={"user_id": "user-1", "key_2": "chat_weather"},
        user_question="What's the weather in Bilbao?",
        chat_api_response="The weather in Bilbao is bad.",
    )
    ai_service.call_llm.assert_called_once_with(
        system_prompt=build_system_prompt(),
        user_prompt=build_user_prompt(question="What's the weather in Bilbao?"),
        max_output_tokens=6666,
        is_chat=True,
        is_rag=False,
        history=[],
        tool_declarations=ChatWeatherTools().declarations(),
        tool_dispatch=service.ai_service.call_llm.call_args.kwargs["tool_dispatch"],
        cache_name=None,
    )
    assert set(ai_service.call_llm.call_args.kwargs["tool_dispatch"]) == {"get_weather"}


def test_chat_weather_get_chat_returns_weather_history(monkeypatch):
    history = [{"chat_log_id": "chat-1", "role": "user", "text": "Weather?"}]
    service = ChatWeatherService()
    monkeypatch.setattr(service, "get_chat_history", Mock(return_value=history))

    assert service.get_chat(user_id="user-1") == history
    service.get_chat_history.assert_called_once_with(user_id="user-1", key_2="chat_weather")
