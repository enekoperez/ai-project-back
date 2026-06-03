from datetime import datetime
import json
from unittest.mock import Mock
import urllib.error

from webapp.prompts.chat_prompt import (
    build_system_prompt,
    build_user_prompt,
    build_weather_system_prompt,
    build_weather_user_prompt,
)
from webapp.services.base_service import BaseService
from webapp.services.chat_service import ChatService
from webapp.tools.chat_tools import ChatTools


def test_chat_service_inherits_base_service():
    assert isinstance(ChatService(), BaseService)


def test_chat_creates_chat_row_and_calls_ai_service_with_question():
    ai_service = Mock()
    ai_service.call_llm.return_value = (
        "Use the OCR endpoint for invoice files.",
        "model",
        1.0,
        None,
        [],
        100,
    )
    chat_log_repository = Mock()
    created_at = datetime(2026, 6, 1, 12, 0, 0)
    chat_log_repository.create.return_value = Mock(id="chat-1", created_at=created_at)
    service = ChatService()
    service.ai_service = ai_service
    service.chat_log_repository = chat_log_repository
    service.rag_service = Mock()
    chat_log_repository.get_history.return_value = []
    service.rag_service.get_top_chunks.return_value = [
        {"source_name": "ocr.md", "score": 0.9, "text": "Use the OCR endpoint for invoice files."}
    ]

    response = service.chat(user_id="user-1", request_json={"question": "  How do I extract invoice totals?  "})

    assert response == {
        "chat_log_id": "chat-1",
        "chat_api_response": "Use the OCR endpoint for invoice files.",
        "date": "2026-06-01T12:00:00",
        "date_utc_in_millis": BaseService._to_millis(created_at),
        "cache_create_time": None,
        "cache_create_time_utc_in_millis": None,
        "source_names_and_scores": [{"source_name": "ocr.md", "score": 0.9}],
    }
    chat_log_repository.create.assert_called_once_with(
        key={"user_id": "user-1"},
        user_question="How do I extract invoice totals?",
        chat_api_response="Use the OCR endpoint for invoice files.",
    )
    service.rag_service.get_top_chunks.assert_called_once_with(question="How do I extract invoice totals?")
    ai_service.call_llm.assert_called_once_with(
        system_prompt=build_system_prompt(),
        user_prompt=build_user_prompt(
            chunks=[{"source_name": "ocr.md", "score": 0.9, "text": "Use the OCR endpoint for invoice files."}],
            question="How do I extract invoice totals?",
        ),
        max_output_tokens=6666,
        is_chat=False,
        is_rag=True,
        history=[],
        tool_declarations=None,
        tool_dispatch=None,
    )


def test_chat_allows_missing_created_at():
    ai_service = Mock()
    ai_service.call_llm.return_value = ("Answer text", "model", 1.0, None, [], 100)
    chat_log_repository = Mock()
    chat_log_repository.create.return_value = Mock(id="chat-1", created_at=None)
    service = ChatService()
    service.ai_service = ai_service
    service.chat_log_repository = chat_log_repository
    service.rag_service = Mock()
    service.rag_service.get_top_chunks.return_value = []

    response = service.chat(user_id="user-1", request_json={"question": "What can this app do?"})

    assert response == {
        "chat_log_id": "chat-1",
        "chat_api_response": "Answer text",
        "date": None,
        "date_utc_in_millis": None,
        "cache_create_time": None,
        "cache_create_time_utc_in_millis": None,
        "source_names_and_scores": [],
    }
    chat_log_repository.create.assert_called_once_with(
        key={"user_id": "user-1"},
        user_question="What can this app do?",
        chat_api_response="Answer text",
    )


def test_weather_chat_uses_tools_without_rag_and_separate_history():
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
    created_at = datetime(2026, 6, 1, 12, 0, 0)
    chat_log_repository.create.return_value = Mock(id="chat-1", created_at=created_at)
    chat_log_repository.get_history.return_value = []
    service = ChatService()
    service.ai_service = ai_service
    service.chat_log_repository = chat_log_repository
    service.rag_service = Mock()

    response = service.weather(
        user_id="user-1",
        request_json={"question": "  What's the weather in Bilbao?  "},
    )

    assert response == {
        "chat_log_id": "chat-1",
        "chat_api_response": "The weather in Bilbao is bad.",
        "date": "2026-06-01T12:00:00",
        "date_utc_in_millis": BaseService._to_millis(created_at),
        "cache_create_time": None,
        "cache_create_time_utc_in_millis": None,
        "source_names_and_scores": [],
    }
    service.rag_service.get_top_chunks.assert_not_called()
    chat_log_repository.get_history.assert_called_once_with(key={"user_id": "user-1", "key_2": "weather"})
    chat_log_repository.create.assert_called_once_with(
        key={"user_id": "user-1", "key_2": "weather"},
        user_question="What's the weather in Bilbao?",
        chat_api_response="The weather in Bilbao is bad.",
    )
    ai_service.call_llm.assert_called_once_with(
        system_prompt=build_weather_system_prompt(),
        user_prompt=build_weather_user_prompt(question="What's the weather in Bilbao?"),
        max_output_tokens=6666,
        is_chat=True,
        is_rag=False,
        history=[],
        tool_declarations=ChatTools().declarations(),
        tool_dispatch=service.ai_service.call_llm.call_args.kwargs["tool_dispatch"],
    )
    assert set(ai_service.call_llm.call_args.kwargs["tool_dispatch"]) == {"get_weather"}


class FakeWeatherResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_weather_tool_returns_open_meteo_current_weather(monkeypatch):
    responses = [
        {
            "results": [
                {
                    "name": "Bilbao",
                    "country": "Spain",
                    "latitude": 43.2627,
                    "longitude": -2.9253,
                }
            ]
        },
        {
            "timezone": "Europe/Madrid",
            "current_units": {
                "temperature_2m": "°C",
                "relative_humidity_2m": "%",
                "wind_speed_10m": "km/h",
            },
            "current": {
                "time": "2026-06-03T18:45",
                "temperature_2m": 21.4,
                "relative_humidity_2m": 63,
                "wind_speed_10m": 9.2,
                "weather_code": 2,
            },
        },
    ]
    requested_urls = []

    def urlopen(req, timeout):
        requested_urls.append(req.full_url)
        return FakeWeatherResponse(responses.pop(0))

    monkeypatch.setattr("webapp.tools.chat_tools.urllib.request.urlopen", urlopen)
    tools = ChatTools()

    assert tools.dispatch()["get_weather"](city="Oviedo") == {
        "city": "Oviedo",
        "resolved_city": "Bilbao",
        "country": "Spain",
        "latitude": 43.2627,
        "longitude": -2.9253,
        "timezone": "Europe/Madrid",
        "time": "2026-06-03T18:45",
        "temperature": 21.4,
        "temperature_unit": "°C",
        "relative_humidity": 63,
        "relative_humidity_unit": "%",
        "wind_speed": 9.2,
        "wind_speed_unit": "km/h",
        "weather_code": 2,
    }
    assert len(requested_urls) == 2
    assert requested_urls[0].startswith("https://geocoding-api.open-meteo.com/v1/search?")
    assert "name=Oviedo" in requested_urls[0]
    assert requested_urls[1].startswith("https://api.open-meteo.com/v1/forecast?")


def test_weather_tool_returns_error_when_city_not_found(monkeypatch):
    requested_urls = []

    def urlopen(req, timeout):
        requested_urls.append(req.full_url)
        return FakeWeatherResponse({})

    monkeypatch.setattr("webapp.tools.chat_tools.urllib.request.urlopen", urlopen)
    tools = ChatTools()

    assert tools.dispatch()["get_weather"](city="Unknown City") == {"error": "City not found", "city": "Unknown City"}
    assert len(requested_urls) == 1
    assert requested_urls[0].startswith("https://geocoding-api.open-meteo.com/v1/search?")


def test_weather_tool_returns_error_when_api_fails(monkeypatch):
    def urlopen(req, timeout):
        raise urllib.error.URLError("network down")

    monkeypatch.setattr("webapp.tools.chat_tools.urllib.request.urlopen", urlopen)
    tools = ChatTools()

    response = tools.dispatch()["get_weather"](city="Bilbao")

    assert response["error"] == "Weather lookup failed"
    assert response["city"] == "Bilbao"
    assert "network down" in response["details"]


def test_get_chat_delegates_to_base_history(monkeypatch):
    service = ChatService()
    history = [{"chat_log_id": "chat-1", "role": "user", "text": "Question"}]
    monkeypatch.setattr(service, "get_chat_history", Mock(return_value=history))

    assert service.get_chat(user_id="user-1") == history
    service.get_chat_history.assert_called_once_with(user_id="user-1")


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
