from datetime import datetime
from unittest.mock import Mock

from webapp.dto.ocr_dto import ocr_to_dict


def test_ocr_to_dict_serializes_created_at_when_present():
    db_obj = Mock(id="ocr-1", created_at=datetime(2026, 6, 1, 12, 0, 0))

    assert ocr_to_dict(db_obj, {"total": ["120.00"]}) == {
        "id": "ocr-1",
        "created_at": "2026-06-01T12:00:00",
        "response": {"total": ["120.00"]},
    }


def test_ocr_to_dict_allows_missing_created_at():
    db_obj = Mock(id="ocr-1", created_at=None)

    assert ocr_to_dict(db_obj, "raw response") == {
        "id": "ocr-1",
        "created_at": None,
        "response": "raw response",
    }
