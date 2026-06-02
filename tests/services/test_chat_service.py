from datetime import datetime
from unittest.mock import Mock

from webapp.prompts.chat_prompt import build_system_prompt, build_user_prompt
from webapp.services.base_service import BaseService
from webapp.services.chat_service import ChatService


def test_chat_service_inherits_base_service():
    assert isinstance(ChatService(), BaseService)


def test_ask_creates_chat_row_and_calls_ai_service_with_question():
    ai_service = Mock()
    ai_service.call_llm.return_value = (
        "Use the OCR endpoint for invoice files.",
        "model",
        1.0,
        None,
        [],
        100,
    )
    chat_repository = Mock()
    chat_repository.create.return_value = Mock(id="chat-1", created_at=datetime(2026, 6, 1, 12, 0, 0))
    service = ChatService()
    service.ai_service = ai_service
    service.chat_repository = chat_repository
    service.rag_service = Mock()
    service.rag_service.get_top_chunks.return_value = [
        {"source_name": "ocr.md", "score": 0.9, "text": "Use the OCR endpoint for invoice files."}
    ]

    response = service.ask({"question": "  How do I extract invoice totals?  "})

    assert response == {
        "id": "chat-1",
        "response": "Use the OCR endpoint for invoice files.",
        "created_at": "2026-06-01T12:00:00",
    }
    chat_repository.create.assert_called_once_with()
    service.rag_service.get_top_chunks.assert_called_once_with(question="How do I extract invoice totals?")
    ai_service.call_llm.assert_called_once_with(
        system_prompt=build_system_prompt(),
        user_prompt=build_user_prompt(
            chunks=[{"source_name": "ocr.md", "score": 0.9, "text": "Use the OCR endpoint for invoice files."}],
            question="How do I extract invoice totals?",
        ),
        is_rag=True,
    )


def test_ask_allows_missing_created_at():
    ai_service = Mock()
    ai_service.call_llm.return_value = ("Answer text", "model", 1.0, None, [], 100)
    chat_repository = Mock()
    chat_repository.create.return_value = Mock(id="chat-1", created_at=None)
    service = ChatService()
    service.ai_service = ai_service
    service.chat_repository = chat_repository
    service.rag_service = Mock()
    service.rag_service.get_top_chunks.return_value = []

    response = service.ask({"question": "What can this app do?"})

    assert response == {
        "id": "chat-1",
        "response": "Answer text",
        "created_at": None,
    }
