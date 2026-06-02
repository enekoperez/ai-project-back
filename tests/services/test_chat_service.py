from datetime import datetime
from unittest.mock import Mock

from webapp.prompts.chat_prompt import build_system_prompt, build_user_prompt
from webapp.services.base_service import BaseService
from webapp.services.chat_service import ChatService


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
