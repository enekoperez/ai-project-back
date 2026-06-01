from unittest.mock import Mock
from datetime import datetime

from webapp.prompts.ocr_prompt import build_system_prompt, build_user_prompt
from webapp.services.ocr_service import OcrService


def test_ask_creates_ocr_row_and_calls_ai_service_with_file_and_questions():
    ai_service = Mock()
    ai_service.call_llm.return_value = ("The invoice total is 120.00.", "model", 0.0, None, [], 100)
    ocr_repository = Mock()
    ocr_repository.create.return_value = Mock(id="ocr-1", created_at=datetime(2026, 6, 1, 12, 0, 0))
    service = OcrService()
    service.ai_service = ai_service
    service.ocr_repository = ocr_repository

    response = service.ask({
        "file_url": "https://example.com/docs/invoice.PDF?token=abc",
        "questions": ["What is the total?", "What is the invoice number?"],
    })

    assert response == {
        "id": "ocr-1",
        "response": "The invoice total is 120.00.",
        "created_at": "2026-06-01T12:00:00",
    }
    ocr_repository.create.assert_called_once_with()
    ai_service.call_llm.assert_called_once_with(
        system_prompt=build_system_prompt(),
        user_prompt="Answer these questions about the file:\n- What is the total?\n- What is the invoice number?",
        response_format={
            "type": "object",
            "properties": {
                "what is the total?": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "All values found for What is the total?",
                },
                "what is the invoice number?": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "All values found for What is the invoice number?",
                },
            },
            "required": ["what is the total?", "what is the invoice number?"],
        },
        document_data={
            "url": "https://example.com/docs/invoice.PDF?token=abc",
            "extension": "pdf",
        },
    )


def test_build_user_prompt_lists_questions():
    assert build_user_prompt(["First?", "Second?"]) == (
        "Answer these questions about the file:\n"
        "- First?\n"
        "- Second?"
    )
