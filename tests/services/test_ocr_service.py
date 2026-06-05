from datetime import datetime, timezone
from unittest.mock import Mock

from webapp.prompts.ocr_prompt import build_system_prompt
from webapp.services.base_service import BaseService
from webapp.services.ocr_service import OcrService


def test_ocr_service_inherits_base_service():
    assert isinstance(OcrService(), BaseService)


def test_ask_creates_ocr_row_and_calls_ai_service_with_file_and_questions():
    ai_service = Mock()
    ai_service.call_llm.return_value = (
        '{"What is the total?": ["120.00"], "What is the invoice number?": ["INV-1"]}',
        "model",
        0.0,
        None,
        [],
        100,
    )
    ocr_log_repository = Mock()
    ocr_log_repository.create.return_value = Mock(id="ocr-1", created_at=datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc))
    service = OcrService()
    service.ai_service = ai_service
    service.ocr_log_repository = ocr_log_repository

    response = service.ask({
        "file_url": "https://example.com/docs/invoice.PDF?token=abc",
        "questions": ["  What is the total?  ", "  What is the invoice number?  "],
    })

    assert response == {
        "id": "ocr-1",
        "response": {
            "What is the total?": ["120.00"],
            "What is the invoice number?": ["INV-1"],
        },
        "created_at": "2026-06-01T12:00:00+00:00",
    }
    ocr_log_repository.create.assert_called_once_with()
    ai_service.call_llm.assert_called_once_with(
        system_prompt=build_system_prompt(),
        user_prompt=(
            "Answer the following questions about the file: "
            "['What is the total?', 'What is the invoice number?']"
        ),
        response_format={
            "type": "object",
            "properties": {
                "What is the total?": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "All values found for What is the total?",
                },
                "What is the invoice number?": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "All values found for What is the invoice number?",
                },
            },
            "required": ["What is the total?", "What is the invoice number?"],
        },
        document_data={
            "url": "https://example.com/docs/invoice.PDF?token=abc",
            "extension": "pdf",
        },
    )


def test_ask_returns_raw_ai_response_when_response_is_not_valid_json():
    ai_service = Mock()
    ai_service.call_llm.return_value = ("The invoice total is 120.00.", "model", 0.0, None, [], 100)
    ocr_log_repository = Mock()
    ocr_log_repository.create.return_value = Mock(id="ocr-1", created_at=None)
    service = OcrService()
    service.ai_service = ai_service
    service.ocr_log_repository = ocr_log_repository

    response = service.ask({
        "file_url": "https://example.com/docs/invoice.pdf",
        "questions": ["What is the total?"],
    })

    assert response == {
        "id": "ocr-1",
        "response": "The invoice total is 120.00.",
        "created_at": None,
    }


def test_try_json_loads_returns_non_string_values_unchanged():
    value = {"already": "decoded"}

    assert OcrService._try_json_loads(value) is value


def test_response_format_supports_empty_question_list():
    assert OcrService()._response_format([]) == {
        "type": "object",
        "properties": {},
        "required": [],
    }
