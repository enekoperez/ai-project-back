from datetime import datetime, timezone
from unittest.mock import Mock

from webapp.dto.chat_dto import chat_to_dict


def test_chat_to_dict_serializes_created_at_when_present():
    db_obj = Mock(id="chat-1", created_at=datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc))

    assert chat_to_dict(db_obj, "Answer text") == {
        "id": "chat-1",
        "created_at": "2026-06-01T12:00:00+00:00",
        "response": "Answer text",
    }


def test_chat_to_dict_allows_missing_created_at():
    db_obj = Mock(id="chat-1", created_at=None)

    assert chat_to_dict(db_obj, "Answer text") == {
        "id": "chat-1",
        "created_at": None,
        "response": "Answer text",
    }
